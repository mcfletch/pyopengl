"""Generation reads data, not the friendly modules.

A friendly module's customisation chain is a *second* copy of what
``annotations.json`` holds.  While the tree still carries chains the two can be
compared, which is how the table is kept honest -- but the generator must not
*read* them, because migrating a module deletes its chain and anything only the
chain held would go with it.

That is not hypothetical.  ``setInputArraySize(name, None)`` was recorded only
for its length, so migrating a module dropped the conversion; and ``retains``,
which decides the client-array family, lived only in ``setStoreValues``.  Both
were invisible until something compared the two paths, so the comparison is a
test rather than a habit.
"""

import os

import pytest

from cdispatch import annotations, emit_c, extract

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def from_chains():
    return extract.extract_tree(PACKAGE, read_chains=True)


@pytest.fixture(scope='module')
def from_data():
    return extract.extract_tree(PACKAGE, read_chains=False)


class TestTheTwoPathsAgree:
    def test_the_same_commands_are_found(self, from_chains, from_data):
        assert set(from_chains) == set(from_data)

    def test_every_stub_is_byte_identical(self, from_chains, from_data):
        """The acceptance criterion: reading the chains changes no C."""
        differing = []
        for key in sorted(set(from_chains)):
            with_chain, without = from_chains[key], from_data[key]
            left = emit_c.emit_stub(with_chain) if emit_c.is_emittable(with_chain) else None
            right = emit_c.emit_stub(without) if emit_c.is_emittable(without) else None
            if left != right:
                differing.append(key)
        assert differing == []

    def test_the_same_commands_are_emittable(self, from_chains, from_data):
        """A command must not appear in, or vanish from, the C either way."""
        left = {key for key, c in from_chains.items() if emit_c.is_emittable(c)}
        right = {key for key, c in from_data.items() if emit_c.is_emittable(c)}
        assert left == right

    def test_the_table_comes_out_the_same(self, from_chains, from_data):
        assert annotations.dump(from_data) == annotations.dump(from_chains)

    def test_the_records_match_field_by_field(self, from_chains, from_data):
        """Not just the dumped view, which could hide a field it omits."""
        for key, expected in from_chains.items():
            actual = from_data[key]
            assert actual.helper == expected.helper, key
            assert actual.retains == expected.retains, key
            for a, b in zip(actual.parameters, expected.parameters):
                assert a.direction == b.direction, (key, a.name)
                assert a.size == b.size, (key, a.name)
                assert a.retain == b.retain, (key, a.name)
                assert a.converts == b.converts, (key, a.name)
                assert a.output_order == b.output_order, (key, a.name)


class TestWhatTheTableHasToCarry:
    """The facts that were lost, named so that losing them again fails here."""

    def test_a_conversion_with_no_known_length_is_recorded(self, from_data):
        """``setInputArraySize(name, None)``, which is most of them."""
        command = from_data[('GL', 'glBufferStorage')]
        data = next(p for p in command.parameters if p.name == 'data')
        assert data.converts is True

    def test_a_void_pointer_argument_is_still_known_to_be_an_array(self, from_data):
        """The declared type cannot answer: it may be an offset into a buffer."""
        command = from_data[('GL', 'glDrawElementsInstancedBaseInstance')]
        indices = next(p for p in command.parameters if p.name == 'indices')
        assert indices.converts is True

    def test_a_client_array_registration_is_recorded(self, from_data):
        """``retains`` decides the family and the pointer's size."""
        assert from_data[('GL', 'glVertexPointer')].retains is True

    def test_a_retained_pointer_gets_its_size(self, from_data):
        """glEdgeFlagPointer has no type argument, so the size is the default."""
        command = from_data[('GL', 'glEdgeFlagPointer')]
        pointer = next(p for p in command.parameters if p.name == 'pointer')
        assert pointer.retain is True
        assert pointer.size is not None


class TestTheGeneratorSaysSo:
    def test_generate_does_not_read_the_chains(self):
        """Stated in the call, so that a future edit has to mean it."""
        import inspect

        from cdispatch import generate

        source = inspect.getsource(generate.generate)
        assert 'read_chains=False' in source
