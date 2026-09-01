"""Arrays whose element type is chosen at run time.

``glDrawElements(mode, count, type, indices)`` says what its indices are made
of in the ``type`` argument, so the element type is not a property of the
signature -- it is a value the caller passes.  The same shape covers the
client-side array pointers, where the GL additionally keeps the memory after
the call returns.
"""

import os

import pytest

from cdispatch import emit_c, extract, model

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(HERE, 'OpenGL')
REGISTRY = os.path.join(HERE, 'src', 'khronosapi', 'xml')

pytestmark = pytest.mark.skipif(
    not os.path.isdir(REGISTRY), reason='no Khronos registry checked out'
)


@pytest.fixture(scope='module')
def commands():
    return extract.extract_tree(PACKAGE)


class TestTypedArrays:
    def test_draw_elements_indices_are_typed(self, commands):
        command = commands[('GL', 'glDrawElements')]
        indices = command.parameters[-1]
        assert isinstance(indices.size, model.TypedArray)
        names = [p.name for p in command.parameters]
        assert names[indices.size.type_argument] == 'type'

    def test_a_client_pointer_is_typed_and_retained(self, commands):
        command = commands[('GL', 'glInterleavedArrays')]
        pointer = command.parameters[-1]
        assert isinstance(pointer.size, model.TypedArray)
        assert pointer.retain

    def test_a_draw_call_is_not_retained(self, commands):
        """glDrawElements reads its indices during the draw and keeps nothing."""
        assert not commands[('GL', 'glDrawElements')].parameters[-1].retain

    def test_the_pointer_family_keeps_its_ctypes_binding(self, commands):
        """pointers.py builds them by mutating a wrapper in place.

        An entry point of ours cannot take part in that, because the builder
        throws the return value away.
        """
        from cdispatch import handwritten

        for name in handwritten.EXCLUDED:
            command = commands.get(('GL', name))
            if command is None:
                continue
            assert not emit_c.is_emittable(command), name
            assert emit_c.exclusion_reason(command) == (
                'built in place by the Python layer'
            )


class TestCompressedImages:
    """A compressed image carries its own size, so nothing is computed."""

    def test_it_is_emitted(self, commands):
        assert emit_c.is_emittable(commands[('GL', 'glCompressedTexImage2D')])

    def test_its_data_is_a_plain_input_array(self, commands):
        data = commands[('GL', 'glCompressedTexImage2D')].parameters[-1]
        assert data.size is model.NO_SIZE
        assert not data.is_output


class TestEmission:
    def test_a_typed_array_names_its_type_argument(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glDrawElements')])
        assert 'PYGL_ARRAY_TYPED(3, indices, type, 0);' in text

    def test_a_retained_pointer_says_so(self, commands):
        text = emit_c.emit_stub(commands[('GL', 'glInterleavedArrays')])
        assert 'PYGL_ARRAY_TYPED(2, pointer, 0, 1);' in text
        assert 'pygl_retain' in text

    def test_both_families_are_emitted(self, commands):
        for name in (
            'glDrawElements',
            'glDrawElementsBaseVertex',
            'glDrawRangeElements',
            'glInterleavedArrays',
        ):
            assert emit_c.is_emittable(commands[('GL', name)]), name

class TestVariadicConvenience:
    """A convenience signature on top does not stop the C implementing the
    entry point underneath.

    ``OpenGL.GL.exceptional`` gives glBufferData a three-argument form that
    works the size out from the array.  That wrapper is a thin Python function
    which calls the entry point; the entry point itself is ordinary, and the
    marshalling belongs in the C either way.
    """

    def test_the_entry_point_is_still_emitted(self, commands):
        for name in ('glBufferData', 'glCallLists', 'glDeleteTextures'):
            command = commands[('GL', name)]
            assert command.helper == 'variadic', name
            assert emit_c.is_emittable(command), name

    def test_it_is_not_marked_as_implementing_the_friendly_form(self, commands):
        """The convenience signature is the Python layer's, and stays there.

        So a customisation call on it must still demote rather than be
        swallowed -- the C implements the entry point, not the wrapper.
        """
        assert not emit_c.implements_friendly(commands[('GL', 'glBufferData')])
