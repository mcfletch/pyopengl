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
import paths
import re
import glob
import json
import unittest

ROOT = paths.ROOT
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


#: Context state that answers with a list, and the query saying how long the
#: list is.  Each of these is "params returns GL_NUM_... values" in the
#: specification, so the size has to be read from that query rather than
#: fixed: a driver with two formats writes two values, and a table saying one
#: hands it an array with room for one.
#:
#: Not every ``GL_NUM_X``/``GL_X`` pair of names is such a pair.
#: ``GL_ACTIVE_VARIABLES`` and ``GL_COMPATIBLE_SUBROUTINES`` are properties of
#: a program resource, read with ``glGetProgramResourceiv`` and
#: ``glGetActiveSubroutineUniformiv``, so no context-wide query answers for
#: them; ``GL_EXTENSIONS`` is a string. The two that are still fixed at one
#: carry a ``#TODO Review`` in ``glgetsizes.csv`` naming the extension text to
#: read: ``GL_DOWNSAMPLE_SCALES_IMG`` and
#: ``GL_SUPPORTED_MULTISAMPLE_MODES_AMD``.
COUNTED_BY_ANOTHER_QUERY = [
    ('GL_COMPRESSED_TEXTURE_FORMATS', 'GL_NUM_COMPRESSED_TEXTURE_FORMATS', 1),
    ('GL_SHADER_BINARY_FORMATS', 'GL_NUM_SHADER_BINARY_FORMATS', 1),
    ('GL_PROGRAM_BINARY_FORMATS', 'GL_NUM_PROGRAM_BINARY_FORMATS', 1),
    # Each mode is a pair -- coverage samples and colour samples -- so this one
    # is two values per mode.  NV_framebuffer_multisample_coverage.
    ('GL_MULTISAMPLE_COVERAGE_MODES_NV',
     'GL_MAX_MULTISAMPLE_COVERAGE_MODES_NV', 2),
]


def _declared(path):
    """``{name: (value, size expression)}`` for one generated module."""
    found = {}
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            matched = _LINE.match(line.strip())
            if matched:
                value, size, name = matched.groups()
                found[name] = (value, _bare(size))
    return found


class TestALengthTheDriverDecidesIsAskedFor(unittest.TestCase):
    """A fixed size for one of these is not a wrong answer but a short buffer.

    The driver is handed an array sized from the table and writes as many
    values as it has, so a table that says one where the driver has two is a
    write past the end of that array.
    """

    def test_the_size_is_read_from_the_query_that_gives_it(self):
        offenders = []
        for path in glob.glob(
            os.path.join(ROOT, 'OpenGL', 'raw', '*', '_glgets.py')
        ):
            api = os.path.basename(os.path.dirname(path))
            declared = _declared(path)
            for name, counter, components in COUNTED_BY_ANOTHER_QUERY:
                if name not in declared or counter not in declared:
                    continue
                value = declared[counter][0]
                wanted = ('(_L(%s),)' % (value,) if components == 1
                          else '(%d,_L(%s),)' % (components, value))
                found = declared[name][1]
                if found != wanted:
                    offenders.append(
                        '  [%s] %s is %s, and %s says how many there are, so '
                        'it should be %s' % (api, name, found, counter, wanted)
                    )
        self.assertEqual(
            offenders, [],
            'a glGet whose length the driver decides is declared fixed:\n'
            + '\n'.join(offenders),
        )


class TestTheSnapshotsAgreeWithTheTable(unittest.TestCase):
    """``tests/<suite>/glget_groups.json`` records each pname's size beside the
    getter family it belongs to, so the size suite can ask what a feature
    defines without parsing the registry.  It is generated from the CSV by
    ``src/glget_groups_gen.py``.

    A CSV edit that does not regenerate it leaves the suite asserting the size
    that was corrected, and the correction has no effect on what is checked --
    which is how ``GL_PROGRAM_BINARY_FORMATS`` went on being asked for as one
    value on a driver that has none.
    """

    def test_every_recorded_size_is_the_one_the_table_states(self):
        from regen_glgets import load_csv

        table = dict(load_csv())
        offenders = []
        for path in sorted(
            glob.glob(os.path.join(ROOT, 'tests', '*', 'glget_groups.json'))
        ):
            suite = os.path.basename(os.path.dirname(path))
            with open(path, encoding='utf-8') as handle:
                data = json.load(handle)
            for kind in ('features', 'extensions'):
                for entry in data.get(kind, {}).values():
                    for descriptor in entry.get('glgets', ()):
                        stated = table.get(descriptor['name'])
                        if stated is not None and stated != descriptor['size']:
                            offenders.append(
                                '  [%s] %s is %r, and glgetsizes.csv states %r'
                                % (suite, descriptor['name'],
                                   descriptor['size'], stated)
                            )
        self.assertEqual(
            sorted(set(offenders)), [],
            'a snapshot disagrees with the size table; run '
            'python src/glget_groups_gen.py\n'
            + '\n'.join(sorted(set(offenders))),
        )


if __name__ == '__main__':
    unittest.main()
