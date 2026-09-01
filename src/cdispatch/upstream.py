"""Compare the shipped bindings against the Khronos registry.

The registry gains entry points and enums continuously, and the useful question
after a pull is a short one: what is new, what changed, and does any of it need
a person to look at it?  :func:`compare` answers that, and
``src/check_registry.py`` prints it.
"""

import json
import os
from dataclasses import dataclass, field

from . import emit_c, extract

__all__ = ['Report', 'compare', 'load_baseline', 'new_drift', 'write_baseline']

#: Differences between the shipped tree and the registry that are already
#: known and explained.  Recorded so that new drift is a failure while the
#: existing lag stays visible instead of silently tolerated.
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'registry_baseline.json')

#: The registry files vendored under ``src/khronosapi/xml``.  EGL's registry is
#: a separate repository and is not vendored, so the EGL bindings are compared
#: against nothing here and are simply not reported on.
REGISTRY_FILES = ('gl.xml', 'glx.xml', 'wgl.xml')

#: EGL is a separate Khronos repository; extract.registry_files() knows where
#: src/fetch_registries.py puts it.

#: Which registry API name maps to which of PyOpenGL's namespaces.  A command
#: can be required by several, so the comparison accepts a binding in any of
#: the namespaces the registry offers it to.
API_ALIASES = {
    'gl': ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2'),
    'glx': ('GLX',),
    'wgl': ('WGL',),
}


@dataclass
class Report:
    """What the shipped tree and the registry disagree about."""

    #: Registry commands with no binding at all.
    missing: list = field(default_factory=list)
    #: Bindings whose argument count disagrees with the registry.
    arity_mismatches: list = field(default_factory=list)
    #: Bindings whose argument names disagree with the registry.
    name_mismatches: list = field(default_factory=list)
    #: Bindings PyOpenGL ships that the registry does not define.  Not a
    #: defect: the GLU, GLUT and GLE bindings are hand-maintained, and vendor
    #: extensions are sometimes shipped ahead of the registry.
    extra: list = field(default_factory=list)
    #: Registry commands present but not implemented in C, with the reason.
    not_emitted: dict = field(default_factory=dict)
    #: Registry enums with no constant.
    missing_enums: list = field(default_factory=list)

    @property
    def needs_attention(self):
        """Whether anything here should stop an automated regeneration."""
        return bool(self.missing or self.arity_mismatches or self.name_mismatches)

    def summary(self):
        lines = [
            'registry commands with no binding: %d' % (len(self.missing),),
            'bindings with the wrong arity:     %d' % (len(self.arity_mismatches),),
            'bindings with different arg names: %d' % (len(self.name_mismatches),),
            'registry enums with no constant:   %d' % (len(self.missing_enums),),
            'bindings not implemented in C:     %d'
            % (sum(len(v) for v in self.not_emitted.values()),),
        ]
        for reason, names in sorted(
            self.not_emitted.items(), key=lambda item: -len(item[1])
        ):
            lines.append('    %5d  %s' % (len(names), reason))
        return '\n'.join(lines)


def _registry_commands(registry_root):
    """``{name: (arg_names, api)}`` for every command the registry defines."""
    import sys

    source = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if source not in sys.path:
        sys.path.insert(0, source)
    import xmlreg

    commands = {}
    enums = {}
    from . import extract as _extract

    for path in _extract.registry_files(registry_root):
        filename = os.path.basename(path)
        registry = xmlreg.parse(path)
        api = os.path.splitext(filename)[0]
        for name, command in registry.command_set.items():
            commands[name] = (list(command.argNames), api)
        for name, enum in registry.enumeration_set.items():
            enums[name] = enum.value
    return commands, enums


def _shipped_enums(package_root):
    """Every constant name the shipped raw modules define."""
    import ast

    names = set()
    raw_root = os.path.join(package_root, 'raw')
    for directory, _folders, files in os.walk(raw_root):
        if '__pycache__' in directory:
            continue
        for filename in files:
            if not filename.endswith('.py'):
                continue
            path = os.path.join(directory, filename)
            with open(path, 'r', encoding='utf-8') as handle:
                try:
                    tree = ast.parse(handle.read(), filename=path)
                except SyntaxError:
                    continue
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            names.add(target.id)
    return names


def compare(package_root, registry_root):
    """Compare the shipped bindings with the registry."""
    shipped = extract.extract_tree(package_root)
    by_name = {}
    for (api, name), command in shipped.items():
        by_name.setdefault(name, []).append((api, command))

    registry, registry_enums = _registry_commands(registry_root)
    report = Report()

    for name, (arg_names, api) in sorted(registry.items()):
        candidates = by_name.get(name)
        if not candidates:
            report.missing.append(name)
            continue
        allowed = API_ALIASES.get(api, ())
        matching = [c for owner, c in candidates if owner in allowed] or [
            c for _owner, c in candidates
        ]
        command = matching[0]
        if len(command.parameters) != len(arg_names):
            report.arity_mismatches.append(
                '%s: registry %d, shipped %d'
                % (name, len(arg_names), len(command.parameters))
            )
        elif command.arg_names != arg_names:
            report.name_mismatches.append(
                '%s: registry %r, shipped %r' % (name, arg_names, command.arg_names)
            )

    for name in sorted(by_name):
        if name not in registry:
            report.extra.append(name)

    for key, command in sorted(shipped.items()):
        if emit_c.is_emittable(command):
            continue
        reason = emit_c.exclusion_reason(command) or 'unexplained'
        report.not_emitted.setdefault(reason, []).append('%s.%s' % key)

    shipped_enum_names = _shipped_enums(package_root)
    report.missing_enums = sorted(
        name for name in registry_enums if name not in shipped_enum_names
    )
    return report


def load_baseline(path=BASELINE):
    """The recorded set of known differences."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def new_drift(report, baseline=None):
    """What this report holds that the baseline does not.

    This is the question a scheduled regeneration job asks: not "is the tree
    complete", which it is not and has not been, but "did this registry pull
    change anything nobody has looked at".
    """
    baseline = load_baseline() if baseline is None else baseline
    known_commands = set(baseline.get('missing_commands', {}).get('names', ()))
    known_names = set(baseline.get('argument_name_differences', {}).get('entries', ()))
    known_enums = set(baseline.get('missing_enums', {}).get('names', ()))
    return {
        'missing_commands': [n for n in report.missing if n not in known_commands],
        'argument_name_differences': [
            n for n in report.name_mismatches if n not in known_names
        ],
        'arity_mismatches': list(report.arity_mismatches),
        'missing_enums': [n for n in report.missing_enums if n not in known_enums],
    }


def write_baseline(report, path=BASELINE):
    """Record the current differences as the accepted set.

    Run this after a deliberate regeneration, so that what remains is what
    somebody has looked at.
    """
    existing = load_baseline(path)
    baseline = {
        '_comment': existing.get(
            '_comment',
            [
                'Where the shipped bindings and the vendored Khronos registry',
                'differ today.  Recorded so that new drift is a failure while',
                'the known differences stay visible.',
            ],
        ),
        'missing_commands': {
            '_reason': existing.get('missing_commands', {}).get('_reason', ''),
            'names': sorted(report.missing),
        },
        'argument_name_differences': {
            '_reason': existing.get('argument_name_differences', {}).get('_reason', ''),
            'entries': sorted(report.name_mismatches),
        },
        'missing_enums': {
            '_reason': existing.get('missing_enums', {}).get('_reason', ''),
            'names': sorted(report.missing_enums),
        },
    }
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(baseline, handle, indent=2)
        handle.write('\n')
    return baseline
