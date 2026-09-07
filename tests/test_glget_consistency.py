#! /usr/bin/env python3
"""Static invariants for the glGet output-size tables (no GL context needed).

The size map is keyed by enum *value*, so when two enum names share a value the
last one written wins at runtime.  If their recorded sizes disagree, the winner
silently clobbers the others -- truncating or over-allocating real queries.  This
test fails if any value carries conflicting sizes, in any of the per-API
``_glgets.py`` modules, so a future ``glgetsizes.csv`` edit cannot reintroduce the
class of bug fixed for GL_CURRENT_SECONDARY_COLOR, GL_BUFFER_USAGE, etc.
"""

import os
import re
import glob
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINE = re.compile(r'^_m\[([^\]]+)\]\s*=\s*(.*?)\s*#\s*([A-Za-z0-9_]+)\s*$')


def _bare(size):
    """Size expression without the trailing ``#TODO`` comment or spaces."""
    return size.split('#', 1)[0].strip().replace(' ', '')


def _conflicts(path):
    by_value = {}
    with open(path, encoding='utf-8') as handle:
        lines = handle.readlines()
    for line in lines:
        m = _LINE.match(line.strip())
        if not m:
            continue
        value, size, name = m.groups()
        by_value.setdefault(value, {}).setdefault(_bare(size), []).append(name)
    return {v: sizes for v, sizes in by_value.items() if len(sizes) > 1}


class TestGLGetSizeConsistency(unittest.TestCase):
    def test_no_conflicting_sizes(self):
        offenders = {}
        for path in glob.glob(os.path.join(ROOT, 'OpenGL', 'raw', '*', '_glgets.py')):
            conf = _conflicts(path)
            if conf:
                offenders[os.path.basename(os.path.dirname(path))] = conf
        self.assertEqual(
            offenders, {},
            'enum values with conflicting glGet sizes (alias clobber):\n' +
            '\n'.join(
                '  [%s] %s: %s' % (api, v, dict(sizes))
                for api, conf in offenders.items() for v, sizes in conf.items()
            ),
        )


if __name__ == '__main__':
    unittest.main()
