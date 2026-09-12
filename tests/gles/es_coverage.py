#! /usr/bin/env python3
"""Measure OpenGL-ES entry-point test coverage for this checkout.

Counts the ``gl*`` commands defined per ES level (and per supported extension
module), scans the suite for the commands it calls, and reports coverage.  Run
directly to print a summary; ``--uncovered`` lists what nothing calls.
"""

import os
import paths
import sys
import coverage_scan
import json

HERE = os.path.dirname(os.path.abspath(__file__))
# repo root holding the ``OpenGL`` package (this file lives in tests/gles/)
ROOT = paths.ROOT

#: The declaration table each ES level's commands are declared in, and the name
#: to report it under.  Each bucket holds the commands *introduced* at that
#: level -- 3.x builds on 2.0, so the buckets are disjoint.
LEVEL_MODULES = [
    ('GLES2.0', 'OpenGL.raw.GLES2.VERSION.GLES2_2_0'),
    ('GLES3.0', 'OpenGL.raw.GLES3.VERSION.GLES3_3_0'),
    ('GLES3.1', 'OpenGL.raw.GLES3.VERSION.GLES3_3_1'),
    ('GLES3.2', 'OpenGL.raw.GLES2.ES.VERSION_3_2'),
]


def declarations():
    """The shipped tables the raw modules are built from.

    The tables rather than the compiled extension, which is None wherever
    accelerate is not installed -- and the two describe the same set.
    """
    from OpenGL import _declarations

    return _declarations.data_declarations()


def defined_funcs(module):
    """The ``gl*`` commands a declaration table's module declares.

    Read from the table rather than by scanning a file for ``def gl``: the
    generated modules stopped being files, and a scan for them then reported
    nothing at all for every level while printing a table that looked as
    though it had run.
    """
    contents = declarations().module_contents(module) or {}
    # Each command is (name, argument names, ctypes signature).
    return {entry[0] for entry in contents.get('commands') or ()}


def called_funcs():
    """Commands the suite names, including through the shared base class."""
    return coverage_scan.called(HERE, 'gl')


def extension_sources():
    """``{'GL_VENDOR_name': (module, commands)}`` for the ES extensions."""
    table = declarations()
    out = {}
    for module in table.module_names():
        parts = module.split('.')
        if len(parts) != 5 or parts[:3] != ['OpenGL', 'raw', 'GLES2']:
            if len(parts) != 5 or parts[:3] != ['OpenGL', 'raw', 'GLES3']:
                continue
        vendor, name = parts[3], parts[4]
        if vendor in ('VERSION', 'ES') or name.startswith('_'):
            continue
        funcs = defined_funcs(module)
        if funcs:
            out['GL_%s_%s' % (vendor, name)] = (module, funcs)
    return out


def level_report():
    used = called_funcs()
    rows = []
    for name, module in LEVEL_MODULES:
        defined = defined_funcs(module)
        covered = defined & used
        rows.append((name, defined, covered))
    return used, rows


def extension_report(used):
    """Coverage of the supported extensions snapshotted in the JSON file."""
    path = os.path.join(HERE, 'supported_extensions.json')
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        snap = json.load(fh)['with_funcs']
    total = sorted(set().union(*snap.values())) if snap else []
    covered = [f for f in total if f in used]
    per_ext = []
    for ext, funcs in sorted(snap.items()):
        c = [f for f in funcs if f in used]
        per_ext.append((ext, funcs, c))
    return total, covered, per_ext


def main():
    used, rows = level_report()
    print('%-9s %6s %7s %6s' % ('level', 'total', 'covered', 'pct'))
    for name, defined, covered in rows:
        pct = (100.0 * len(covered) / len(defined)) if defined else 0.0
        print('%-9s %6d %7d %5.1f%%' % (name, len(defined), len(covered), pct))

    ext = extension_report(used)
    if ext:
        total, covered, per_ext = ext
        pct = (100.0 * len(covered) / len(total)) if total else 0.0
        print(
            '%-9s %6d %7d %5.1f%%  (supported extensions)'
            % ('EXT', len(total), len(covered), pct)
        )
        if '--ext' in sys.argv:
            for name, funcs, c in per_ext:
                print('  %-46s %2d/%2d' % (name, len(c), len(funcs)))

    if '--uncovered' in sys.argv:
        for name, defined, covered in rows:
            missing = sorted(defined - covered)
            print('\n# %s uncovered (%d):' % (name, len(missing)))
            print(' '.join(missing))
    if '--ext-uncovered' in sys.argv and ext:
        for name, funcs, _c in ext[2]:
            missing = [f for f in funcs if f not in used]
            if missing:
                print('# %s (%d left): %s' % (name, len(missing), ' '.join(missing)))


if __name__ == '__main__':
    main()
