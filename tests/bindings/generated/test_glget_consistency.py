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


#: Entry points whose output is sized from an argument that is not an enum,
#: and what the registry says their length really is.  Each is a ``COMPSIZE``
#: over an object name: the count is held by the object and is read back with
#: a query of its own, so there is no argument to size the array from and the
#: caller passes one.  They are listed here so that the case below asks about
#: the rest, and so that a new one is a failure rather than a nineteenth line
#: nobody looked at.
#:
#: ``glGetVariantBooleanvEXT`` and its eight relatives are
#: ``COMPSIZE(id)``: the length is the datatype the variant was declared with.
#: ``glGetPathCommandsNV`` and its five are ``COMPSIZE(path)``: the length is
#: ``GL_PATH_COMMAND_COUNT_NV`` for that path, from ``glGetPathParameterivNV``.
UNSIZEABLE_OUTPUTS = {
    ('GL', 'glGetInvariantBooleanvEXT'),
    ('GL', 'glGetInvariantFloatvEXT'),
    ('GL', 'glGetInvariantIntegervEXT'),
    ('GL', 'glGetLocalConstantBooleanvEXT'),
    ('GL', 'glGetLocalConstantFloatvEXT'),
    ('GL', 'glGetLocalConstantIntegervEXT'),
    ('GL', 'glGetVariantBooleanvEXT'),
    ('GL', 'glGetVariantFloatvEXT'),
    ('GL', 'glGetVariantIntegervEXT'),
    ('GL', 'glGetVariantPointervEXT'),
    ('GL', 'glGetPathCommandsNV'),
    ('GL', 'glGetPathCoordsNV'),
    ('GL', 'glGetPathDashArrayNV'),
    ('GLES2', 'glGetPathCommandsNV'),
    ('GLES2', 'glGetPathCoordsNV'),
    ('GLES2', 'glGetPathDashArrayNV'),
}


class TestWhatIsSizedFromTheGLGetTable(unittest.TestCase):
    """An output sized from the table has to name an enum to look up.

    ``setOutput(size=_glget_size_mapping, pnameArg='pname')`` allocates the
    answer by looking the value of ``pname`` up among the ``glGet`` sizes.
    Where that argument is a count or an object name rather than an enum, the
    lookup asks what size the enum ``3`` is: a value the table happens to hold
    answers one element for the driver to write every value into, and a value
    it does not raises ``KeyError`` from inside the call.

    Read from the shipped tables, which is what a user's installation has.
    """

    def annotations_and_declarations(self):
        from OpenGL import _declarations

        declared = {}
        for api in _declarations.APIS:
            for _module, command, arguments, types in _declarations.declared_commands(api):
                declared.setdefault((api, command), (arguments, types))
        return _declarations.annotations(), declared

    def test_every_one_names_an_enum(self):
        table, declared = self.annotations_and_declarations()
        offenders = []
        for key, entry in sorted(table.items()):
            api, name = key.split('.', 1)
            for parameter, bits in sorted(entry.get('parameters', {}).items()):
                size = bits.get('size') or {}
                if size.get('kind') != 'glget-table':
                    continue
                if (api, name) in UNSIZEABLE_OUTPUTS:
                    continue
                arguments, types = declared.get((api, name), ([], []))
                pname = size['pname']
                if pname not in arguments:
                    offenders.append(
                        '  %s.%s sizes %s from %r, which is not an argument'
                        % (api, name, parameter, pname)
                    )
                    continue
                # types is the result type followed by one per argument.
                stated = types[arguments.index(pname) + 1]
                if 'GLenum' not in stated:
                    offenders.append(
                        '  %s.%s sizes %s by looking %s up among the glGet '
                        'sizes, and %s is %s rather than an enum'
                        % (api, name, parameter, pname, pname, stated)
                    )
        self.assertEqual(
            offenders, [],
            'an output is sized by looking a non-enum argument up in the '
            'glGet size table:\n' + '\n'.join(offenders),
        )

    def test_the_unsizeable_ones_are_still_there(self):
        """A stale exception would make the case above vacuous for them."""
        table, _declared = self.annotations_and_declarations()
        for api, name in sorted(UNSIZEABLE_OUTPUTS):
            entry = table.get('%s.%s' % (api, name))
            self.assertIsNotNone(entry, (api, name))
            kinds = {
                (bits.get('size') or {}).get('kind')
                for bits in entry.get('parameters', {}).values()
            }
            self.assertIn('glget-table', kinds, (api, name))



class TestADamagedTable(unittest.TestCase):
    """A table entry that will not unmarshal is a broken installation, said so."""

    def test_it_raises_import_error_naming_the_module(self):
        from OpenGL import _declarations

        with self.assertRaisesRegex(ImportError, 'OpenGL.raw.GL.damaged'):
            _declarations._decoded('OpenGL.raw.GL.damaged', b'not marshal data')


if __name__ == '__main__':
    unittest.main()
