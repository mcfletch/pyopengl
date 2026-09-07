#! /usr/bin/env python3
"""Report enums a case names that the context it asks for predates.

An enum is only accepted by a context whose version defines it, or by one that
has the extension that introduced it: everything else is ``GL_INVALID_ENUM``.
Drivers differ in how strictly they say so -- Mesa accepts a 4.3 enum in a 3.3
context, macOS refuses it -- so a case that gets this wrong passes on the
machine it was written on and fails on someone else's, with a GL error that
names the call rather than the enum in it.

Run it against the GL suite::

    python tests/gl/enum_age_audit.py

Each finding is a class's declared ``gl_version``, an enum it names, and the
core version that introduced the enum.  A finding is not automatically a
defect: a case that reaches the enum only through ``require_extension``,
``allow_missing``, ``exercise`` or ``tolerate_glerror`` has said it will accept
whatever the driver answers, and is reported as ``tolerated`` rather than
``possible`` so the distinction is visible rather than assumed.

Enums are read from the syntax tree rather than from the text, so a name in a
comment or in a string -- ``getattr(GL, 'GL_SAMPLER')``, which compares a value
and never hands it to the GL -- is not a use.

The registry in ``src/khronosapi`` is the authority for which version
introduced what.
"""

from __future__ import annotations

import ast
import pathlib
import sys
from xml.etree import ElementTree

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
REGISTRY = ROOT / 'src' / 'khronosapi' / 'xml' / 'gl.xml'

#: A block whose body says it will take whatever the driver answers.
TOLERATING = ('require_extension', 'allow_missing', 'exercise', 'tolerate_glerror')


def enums_named(node):
    """Every ``GL_*`` this syntax tree reads, as a bare name or an attribute."""
    found = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id.startswith('GL_'):
            found.add(child.id)
        elif isinstance(child, ast.Attribute) and child.attr.startswith('GL_'):
            found.add(child.attr)
    return found


def core_versions(registry=REGISTRY):
    """``{enum name: (major, minor)}`` -- the first desktop GL version with it."""
    root = ElementTree.parse(registry).getroot()
    introduced = {}
    for feature in root.iter('feature'):
        if feature.get('api') != 'gl':
            continue
        version = tuple(int(part) for part in feature.get('number').split('.'))
        for enum in feature.iter('enum'):
            name = enum.get('name')
            if version < introduced.get(name, version + (1,)):
                introduced[name] = version
    return introduced


def audit(directory, introduced):
    """Yield ``(path, where, declared, enum, needs, verdict)`` for `directory`.

    Per method rather than per class: one case tolerating a GL error says
    nothing about the case beside it, and a class-wide verdict would exempt
    every enum in the file on the strength of a single ``exercise()``.
    """
    for path in sorted(pathlib.Path(directory).glob('test_*.py')):
        source = path.read_text()
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ClassDef):
                continue
            declared = _declared_version(node)
            if declared is None:
                continue
            for method in node.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                verdict = _verdict(method)
                where = '%s.%s' % (node.name, method.name)
                for name in sorted(enums_named(method)):
                    needs = introduced.get(name)
                    if needs and needs > declared:
                        yield (path.name, where, declared, name, needs, verdict)


def _verdict(method):
    """Whether this method has said it will take whatever the driver answers.

    Either by running the call inside one of the tolerating blocks, or by
    asking the context what version it is before making it.
    """
    for child in ast.walk(method):
        if isinstance(child, ast.Attribute) and child.attr in TOLERATING:
            return 'tolerated'
        if isinstance(child, ast.Attribute) and child.attr == 'version':
            return 'tolerated'
    return 'possible'


def _declared_version(node):
    """The ``gl_version`` a class assigns, or None where it assigns none."""
    for statement in node.body:
        if not isinstance(statement, ast.Assign):
            continue
        if getattr(statement.targets[0], 'id', None) != 'gl_version':
            continue
        try:
            return tuple(ast.literal_eval(statement.value))
        except ValueError:
            return None
    return None


def main(argv):
    directory = argv[1] if len(argv) > 1 else HERE
    findings = list(audit(directory, core_versions()))
    for path, name, declared, enum, needs, verdict in findings:
        print(
            '%-34s %-24s ctx %d.%d  %-42s needs %d.%d  %s'
            % (path, name, declared[0], declared[1], enum, needs[0], needs[1], verdict)
        )
    possible = [finding for finding in findings if finding[-1] == 'possible']
    print(
        '\n%d enum%s newer than its context, %d of them outside a tolerating block'
        % (len(findings), '' if len(findings) == 1 else 's', len(possible))
    )
    return 1 if possible else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
