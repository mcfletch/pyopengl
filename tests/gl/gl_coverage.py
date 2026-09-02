#! /usr/bin/env python3
"""Measure desktop-OpenGL entry-point test coverage for this checkout.

Counts the ``gl*`` commands declared per GL version (and per supported extension
module), scans the ``test_*.py`` tests for the commands they call, and reports
coverage.  Run directly for a summary; ``--uncovered`` lists missing per-version
commands, ``--ext`` / ``--ext-uncovered`` report extensions.

``--driver`` answers a different and sharper question: of the entry points *this
machine's driver actually provides*, which does nothing here call?  The registry
lists every command any implementation might have, so coverage against it is a
number about the registry; coverage against what is in front of you is a number
about the suite.  It needs a GL context, and opens a hidden one.
"""

import os
import re
import sys
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo root holding ``OpenGL``

_CALL = re.compile(r'\b(gl[A-Z][A-Za-z0-9_]*)\b')

def version_sources():
    """``(name, commands)`` per GL version, oldest first.

    Read from the declaration tables the layer builds its modules from, which
    is where the commands live: they were files of ``def gl...`` once, and
    scanning for those quietly reported nothing at all once they stopped being.
    """
    from OpenGL._dispatch import _c

    names = []
    for module in _c.module_names():
        if not module.startswith('OpenGL.raw.GL.VERSION.GL_'):
            continue
        tail = module.rsplit('.', 1)[-1]            # GL_1_0
        try:
            order = [int(part) for part in tail[3:].split('_')]
        except ValueError:                          # pragma: no cover - odd name
            continue
        names.append((order, tail, module))
    out = []
    for _order, tail, module in sorted(names):
        contents = _c.module_contents(module) or {}
        # Each command is (name, argument names, ctypes signature).
        out.append((tail, {entry[0] for entry in contents.get('commands') or ()}))
    return out


def provided_by_driver():
    """Every GL entry point this driver exports, as a set of names.

    Asked of the driver through the same resolution a caller's first call
    makes, so the answer is "what a program running here could call" rather
    than "what the registry describes".  Needs a current GL context.
    """
    import OpenGL.GL                                # noqa: F401 - installs dispatch
    from OpenGL import _dispatch

    return {
        name
        for (api, name), proc in _dispatch.entry_points.items()
        if api == 'GL' and bool(proc)
    }


#: The framework beside the cases, which calls entry points on their behalf --
#: read_pixel is glReadPixels, getStringi is glGetStringi.  A case using a
#: helper has exercised what the helper calls, and counting only the case files
#: reported those two as never called by anything.
_FRAMEWORK = ('gltestcase.py', '../glcontext.py', '../glcontext_desktop.py')


def called_funcs():
    used = set()
    paths = glob.glob(os.path.join(HERE, 'test_*.py'))
    paths += [os.path.join(HERE, name) for name in _FRAMEWORK]
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            used.update(_CALL.findall(fh.read()))
    return used


def level_report():
    used = called_funcs()
    rows = []
    for name, defined in version_sources():
        rows.append((name, defined, defined & used))
    return used, rows


def driver_report():
    """What this driver provides and nothing here calls.

    Opens a hidden compatibility context through the suite's own machinery, so
    the entry points resolve exactly as they do for the cases themselves.
    """
    tests = os.path.dirname(HERE)
    for directory in (HERE, tests):
        if directory not in sys.path:
            sys.path.insert(0, directory)
    from glcontext import pick_backend
    from glcontext_desktop import DesktopGLTestCaseBase

    class _Probe(pick_backend(), DesktopGLTestCaseBase):
        profile = 'compatibility'
        gl_version = (4, 5)

        def runTest(self):                          # pragma: no cover - unused
            pass

    probe = _Probe()
    probe.setUp()
    try:
        return provided_by_driver(), called_funcs()
    finally:
        probe.tearDown()


def extension_report(used):
    path = os.path.join(HERE, 'supported_extensions.json')
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        snap = json.load(fh)['with_funcs']
    total = sorted(set().union(*snap.values())) if snap else []
    covered = [f for f in total if f in used]
    per_ext = [
        (ext, funcs, [f for f in funcs if f in used])
        for ext, funcs in sorted(snap.items())
    ]
    return total, covered, per_ext


def main():
    if '--driver' in sys.argv:
        provided, used = driver_report()
        missing = sorted(name for name in provided if name not in used)
        print('provided by this driver: %d' % len(provided))
        print('never called in tests:   %d' % len(missing))
        for name in missing:
            print('  %s' % name)
        return

    used, rows = level_report()
    print('%-8s %6s %7s %6s' % ('version', 'total', 'covered', 'pct'))
    tot = cov = 0
    for name, defined, covered in rows:
        pct = (100.0 * len(covered) / len(defined)) if defined else 0.0
        print('%-8s %6d %7d %5.1f%%' % (name, len(defined), len(covered), pct))
        tot += len(defined)
        cov += len(covered)
    print('%-8s %6d %7d %5.1f%%' % ('TOTAL', tot, cov, 100.0 * cov / tot if tot else 0))

    ext = extension_report(used)
    if ext:
        total, covered, per_ext = ext
        pct = (100.0 * len(covered) / len(total)) if total else 0.0
        print(
            '%-8s %6d %7d %5.1f%%  (supported extensions)'
            % ('EXT', len(total), len(covered), pct)
        )
        if '--ext' in sys.argv:
            for name, funcs, c in per_ext:
                print('  %-46s %2d/%2d' % (name, len(c), len(funcs)))

    if '--uncovered' in sys.argv:
        for name, defined, covered in rows:
            missing = sorted(defined - covered)
            if missing:
                print('\n# %s uncovered (%d):' % (name, len(missing)))
                print(' '.join(missing))
    if '--ext-uncovered' in sys.argv and ext:
        for name, funcs, c in ext[2]:
            missing = [f for f in funcs if f not in used]
            if missing:
                print('# %s (%d left): %s' % (name, len(missing), ' '.join(missing)))


if __name__ == '__main__':
    main()
