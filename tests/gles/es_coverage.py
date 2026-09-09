#! /usr/bin/env python3
"""Measure OpenGL-ES entry-point test coverage for this checkout.

Counts the ``gl*`` commands defined per ES level (and per supported extension
module), scans the suite for the commands it calls, and reports coverage.  Run
directly to print a summary; ``--uncovered`` lists what nothing calls.
"""

import os
import paths
import re
import sys
import coverage_scan
import json

HERE = os.path.dirname(os.path.abspath(__file__))
# repo root holding the ``OpenGL`` package (this file lives in tests/gles/)
ROOT = paths.ROOT

# Per-level source modules; each bucket holds the commands *introduced* at that
# level (3.x builds on 2.0, so the buckets are disjoint).
LEVEL_SOURCES = [
    ('GLES2.0', 'OpenGL/raw/GLES2/VERSION/GLES2_2_0.py'),
    ('GLES3.0', 'OpenGL/raw/GLES3/VERSION/GLES3_3_0.py'),
    ('GLES3.1', 'OpenGL/raw/GLES3/VERSION/GLES3_3_1.py'),
    ('GLES3.2', 'OpenGL/raw/GLES2/ES/VERSION_3_2.py'),
]

_DEF = re.compile(r'^def (gl[A-Za-z0-9_]+)\(', re.MULTILINE)
_CALL = re.compile(r'\b(gl[A-Z][A-Za-z0-9_]*)\b')


def defined_funcs(rel_path):
    path = os.path.join(ROOT, rel_path)
    try:
        with open(path) as fh:
            return set(_DEF.findall(fh.read()))
    except IOError:
        return set()


def called_funcs():
    """Commands the suite names, including through the shared base class."""
    return coverage_scan.called(HERE, 'gl')


def extension_sources():
    """Map 'GL_VENDOR_name' -> raw module path, for ext modules with commands."""
    out = {}
    for base in ('OpenGL/raw/GLES2', 'OpenGL/raw/GLES3'):
        for path in glob.glob(os.path.join(ROOT, base, '*', '*.py')):
            vendor = os.path.basename(os.path.dirname(path))
            if vendor in ('VERSION', 'ES', '__pycache__'):
                continue
            name = os.path.splitext(os.path.basename(path))[0]
            if name.startswith('_'):
                continue
            funcs = defined_funcs(os.path.relpath(path, ROOT))
            if funcs:
                out['GL_%s_%s' % (vendor, name)] = (os.path.relpath(path, ROOT), funcs)
    return out


def level_report():
    used = called_funcs()
    rows = []
    for name, src in LEVEL_SOURCES:
        defined = defined_funcs(src)
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
