"""The annotations, as data rather than as Python to be parsed.

What makes ``glTexImage2D`` take nine arguments in Python and eleven in C is
not in the registry: it was written by people, over years, as chains of
``wrapper.wrapper(...).setOutput(...)`` calls in the friendly modules.  The
registry supplies the signatures; these supply everything else.

Writing them down once turns the generator from something that parses our own
generated Python into something that reads two data files.  The test that
matters is the round trip: what the table says must be exactly what reading the
tree says, or the table is a second source of truth rather than the only one.
"""

import os

import pytest

from cdispatch import annotations, extract, model

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def commands():
    return extract.extract_tree(PACKAGE)


@pytest.fixture(scope='module')
def table(commands):
    return annotations.dump(commands)


class TestWhatIsRecorded:
    def test_only_commands_that_carry_something(self, commands, table):
        """Three quarters of the entry points are plain pass-throughs."""
        assert 1000 < len(table) < 1600
        assert len(table) < len(commands)

    def test_an_output_is_recorded(self, table):
        entry = table['GL.glGenTextures']
        assert entry['parameters']['textures']['out'] is True

    def test_a_fixed_size_is_recorded(self, table):
        """``glBinormal3bvEXT(v)`` takes exactly three."""
        size = table['GL.glBinormal3bvEXT']['parameters']['v']['size']
        assert size == {'kind': 'fixed', 'count': 3}

    def test_a_size_taken_from_another_argument_names_it(self, table):
        size = table['GL.glAreProgramsResidentNV']['parameters']['residences']['size']
        assert size == {'kind': 'from-argument', 'argument': 'n', 'divisor': 1}

    def test_an_unchecked_array_is_not_an_annotation(self, table):
        """``setInputArraySize('value', None)`` says "any length", which is
        what a command with no entry already means."""
        assert 'GL.glUniformMatrix4fv' not in table

    def test_an_image_records_what_it_is_sized_from(self, table):
        size = table['GL.glTexImage2D']['parameters']['pixels']['size']
        assert size['kind'] == 'image'
        assert size['format'] == 'format'
        assert size['type'] == 'type'
        assert size['dimensions'] == ['width', 'height']

    def test_a_glget_records_the_pname_it_switches_on(self, table):
        size = table['GL.glGetIntegerv']['parameters']['data']['size']
        assert size['kind'] == 'glget-table'
        assert size['pname'] == 'pname'

    def test_a_typed_array_records_its_type_argument(self, table):
        size = table['GL.glDrawElements']['parameters']['indices']['size']
        assert size['kind'] == 'typed-array'
        assert size['type'] == 'type'

    def test_a_retained_pointer_says_so(self, table):
        assert table['GL.glVertexPointer']['parameters']['pointer']['retain'] is True

    def test_a_hand_written_family_is_named(self, table):
        assert table['GL.glBufferData']['helper'] == 'variadic'

    def test_parameters_are_named_not_numbered(self, table):
        """A position moves when the registry adds an argument; a name does not."""
        for key, entry in table.items():
            for name in entry.get('parameters', ()):
                assert not name.isdigit(), key


class TestRoundTrip:
    """The point of the exercise: the table has to say exactly what the tree
    says, so that reading the tree can stop."""

    def test_applying_the_table_reproduces_the_annotations(self, commands, table):
        stripped = annotations.without_annotations(commands)
        annotations.apply(stripped, table)
        assert annotations.dump(stripped) == table

    def test_every_annotated_command_survives(self, commands, table):
        stripped = annotations.without_annotations(commands)
        assert annotations.dump(stripped) == {}
        annotations.apply(stripped, table)
        for key in table:
            api, name = key.split('.', 1)
            assert (api, name) in stripped

    def test_the_commands_compare_equal_field_by_field(self, commands, table):
        """Not just the dumped view: the records themselves."""
        stripped = annotations.without_annotations(commands)
        annotations.apply(stripped, table)
        for key, original in commands.items():
            rebuilt = stripped[key]
            assert rebuilt.helper == original.helper, key
            for a, b in zip(rebuilt.parameters, original.parameters):
                assert a.direction == b.direction, (key, a.name)
                assert a.size == b.size, (key, a.name)
                assert a.retain == b.retain, (key, a.name)
                assert a.output_order == b.output_order, (key, a.name)


class TestTheCheckedInTable:
    """The table is a file in the tree, and it has to stay current."""

    def test_it_matches_the_tree(self, table):
        stored = annotations.load()
        assert stored == table, (
            'src/cdispatch/annotations.json is out of date; '
            'run python src/regenerate_c.py --write-annotations'
        )


class TestTheGeneratedCIsUnchanged:
    """The acceptance criterion: annotations from data must produce exactly the
    C that annotations from Python produced, for every entry point."""

    def test_every_stub_is_byte_identical(self, commands):
        from cdispatch import emit_c

        rebuilt = annotations.without_annotations(commands)
        annotations.apply(rebuilt, annotations.load())
        checked = 0
        for key in sorted(commands):
            original, from_table = commands[key], rebuilt[key]
            assert emit_c.is_emittable(original) == emit_c.is_emittable(
                from_table
            ), key
            if not emit_c.is_emittable(original):
                continue
            assert emit_c.emit_stub(original) == emit_c.emit_stub(from_table), key
            checked += 1
        assert checked > 4500, checked
