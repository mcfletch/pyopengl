"""Phase 1 -- lifting the hand-written material out of the generated tree.

The generated ``.py`` files are the ground truth for what the friendly API
promises today: which commands exist, in which module, with which types, and
which customisations each carries.  The extractor reads them into the command
record so that the C generator, the ``.pyi`` and the virtual packages all read
one description in one place.
"""

import os

import pytest

from cdispatch import extract, model

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='module')
def commands():
    """Every binding PyOpenGL ships, keyed by ``(api, name)``."""
    return extract.extract_tree(os.path.join(HERE, 'OpenGL'))


@pytest.fixture(scope='module')
def tree(commands):
    """The desktop GL namespace, keyed by bare command name."""
    return extract.api_view(commands, 'GL')


class TestRawModules:
    def test_finds_a_core_command(self, tree):
        command = tree['glBindTexture']
        assert command.name == 'glBindTexture'
        assert command.arg_names == ['target', 'texture']
        assert command.returns_void

    def test_records_the_extension_name(self, tree):
        assert tree['glBindTexture'].feature == 'GL_VERSION_GL_1_1'
        assert (
            tree['glBindBufferARB'].feature == 'GL_ARB_vertex_buffer_object'
        )

    def test_records_the_api(self, commands):
        assert commands[('GL', 'glBindTexture')].api == 'GL'
        assert commands[('GLX', 'glXChooseVisual')].api == 'GLX'

    def test_the_same_name_in_two_apis_is_two_bindings(self, commands):
        """``glTexImage2D`` is in both GL and GLES2, resolved from different
        libraries, so the name alone does not identify an entry point."""
        assert commands[('GL', 'glTexImage2D')] is not commands[
            ('GLES2', 'glTexImage2D')
        ]
        assert commands[('GLES2', 'glTexImage2D')].api == 'GLES2'

    def test_reads_scalar_argument_types(self, tree):
        command = tree['glBindTexture']
        assert [p.ctype.base for p in command.parameters] == ['GLenum', 'GLuint']

    def test_reads_array_argument_types(self, tree):
        """``arrays.GLuintArray`` is a pointer to GLuint."""
        command = tree['glGenTextures']
        textures = command.parameters[1]
        assert textures.ctype.base == 'GLuint'
        assert textures.ctype.pointers == 1

    def test_reads_void_pointer_arguments(self, tree):
        command = tree['glDrawElements']
        indices = command.parameters[3]
        assert indices.ctype.base == 'void'
        assert indices.ctype.pointers == 1

    def test_reads_a_non_void_return(self, tree):
        assert tree['glIsTexture'].return_type.base == 'GLboolean'
        assert tree['glGetString'].return_type.base == 'GLubyte'
        assert tree['glGetString'].return_type.pointers == 1

    def test_covers_the_whole_tree(self, commands):
        """Every registry command PyOpenGL ships a binding for is extracted."""
        assert len(commands) > 3500


class TestFriendlyAnnotations:
    def test_output_parameter_with_a_size_from_another_argument(self, tree):
        """``setOutput('textures', size=lambda x:(x,), pnameArg='n', orPassIn=True)``."""
        command = tree['glGenTextures']
        textures = command.parameters[1]
        assert textures.direction == model.OUT
        assert textures.size == model.FromArg(argument=0, divisor=1)

    def test_the_divisor_forms_are_recognised(self, tree):
        """``size=lambda x: (x//4,)`` is an argument index and a divisor."""
        divisors = set()
        for command in tree.values():
            for parameter in command.parameters:
                if isinstance(parameter.size, model.FromArg):
                    divisors.add(parameter.size.divisor)
        assert divisors <= {1, 4, 8}, divisors

    def test_fixed_size_input_arrays(self, tree):
        """``setInputArraySize('c', 1)`` is one integer."""
        command = tree['glIndexubv']
        assert command.parameters[0].size == model.Fixed(1)

    def test_unchecked_input_arrays_carry_no_size(self, tree):
        """``setInputArraySize(name, None)`` marks a size that is not checked."""
        command = tree['glBufferData']
        data = {p.name: p for p in command.parameters}['data']
        assert data.size is model.NO_SIZE

    def test_glget_sized_outputs(self, tree):
        """``setOutput(..., size=_glgets.GLGET_SIZES, pnameArg='pname')``."""
        command = tree['glGetIntegerv']
        params = command.parameters[1]
        assert params.direction == model.OUT
        assert params.size == model.GLGetTable(pname_argument=0)

    def test_constant_size_outputs(self, tree):
        """``setOutput('length', size=(1,), orPassIn=True)`` is one integer."""
        command = tree['glGetActiveAttrib']
        length = {p.name: p for p in command.parameters}['length']
        assert length.direction == model.OUT
        assert length.size == model.Fixed(1)

    def test_a_command_the_generator_cannot_describe_names_its_family(self, tree):
        """What is left is the variadic family, which dispatches on arity."""
        assert tree['glCallLists'].helper == 'variadic'
        assert tree['glBufferData'].helper == 'variadic'

    def test_the_client_pointer_family_is_described_rather_than_named(self, tree):
        """It was a hand-written family; the registry describes it instead."""
        command = tree['glVertexPointer']
        assert not command.helper
        assert command.retains
        assert command.parameters[-1].retain

    def test_client_array_pointers_are_retained(self, tree):
        """The GL reads these after the call returns, so they must outlive it."""
        command = tree['glVertexPointer']
        assert command.parameters[-1].retain


class TestTierCensus:
    """The census the plan's design rests on, asserted rather than recalled."""

    def test_most_commands_are_pass_through(self, tree):
        tier1 = [c for c in tree.values() if c.tier == 1]
        assert len(tier1) > 1900

    def test_tier_three_is_a_small_closed_set(self, tree):
        tier3 = [c for c in tree.values() if c.tier == 3]
        assert len(tier3) < 250, sorted(c.name for c in tier3)[:40]

    def test_every_command_lands_in_a_tier(self, tree):
        assert all(command.tier in (1, 2, 3) for command in tree.values())


class TestRegistryCrossCheck:
    """The registry is the authority on how a parameter is sized.

    A friendly module rebinding a command under a helper name is not the only
    evidence that it needs one: ``glReadPixels`` is used by ``images.py``
    through a differently-named wrapper, so reading the friendly modules alone
    marks it as pass-through when its ``pixels`` argument is in fact an image
    sized from format, type and dimensions.
    """

    def test_image_commands_carry_an_image_size(self, tree):
        """The registry says which arguments size the image, so it is described
        rather than handed to a Python family."""
        for name in (
            'glReadPixels',
            'glTexImage1D',
            'glTexImage2D',
            'glTexImage3D',
            'glTexSubImage2D',
            'glDrawPixels',
        ):
            pixels = [
                p for p in tree[name].parameters if isinstance(p.size, model.ImageSize)
            ]
            assert pixels, name

    def test_compressed_images_need_no_sizing(self, tree):
        """A compressed image is given its size, so nothing is computed."""
        command = tree['glCompressedTexImage2D']
        assert not command.helper
        assert command.parameters[-1].size is model.NO_SIZE

    def test_an_ordinary_command_is_not_marked(self, tree):
        assert not tree['glBindTexture'].helper
        assert not tree['glGenTextures'].helper
        assert not tree['glUniformMatrix4fv'].helper


class TestOutputOrdering:
    """A multi-output return follows the order the outputs were annotated.

    ``glGetShaderPrecisionFormat`` declares ``range`` before ``precision`` in
    its C signature but annotates ``precision`` first, and the tuple its
    callers unpack follows the annotation.
    """

    def test_the_tuple_follows_the_annotation_order(self, commands):
        command = commands[('GLES2', 'glGetShaderPrecisionFormat')]
        assert [p.name for p in command.output_parameters] == ['precision', 'range']
        assert [p.name for p in command.parameters][2:] == ['range', 'precision']

    def test_a_single_output_needs_no_ordering(self, tree):
        command = tree['glGenTextures']
        assert [p.name for p in command.output_parameters] == ['textures']
