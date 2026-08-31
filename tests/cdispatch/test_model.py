"""The command record every generated artifact is derived from.

One record per entry point, carrying the registry's facts and the annotation
file's, is what the plan calls the clean final model: the friendly API stops
being customisation calls scattered across the tree and becomes a table.
"""

import pytest

from cdispatch import model
from cdispatch.ctypes_model import parse_type


def make_parameter(name='value', declaration='const GLfloat *', **kwargs):
    return model.Parameter(name=name, ctype=parse_type(declaration), **kwargs)


class TestSizeSpec:
    def test_none_is_the_default(self):
        assert make_parameter().size is model.NO_SIZE

    def test_fixed_size_carries_a_count(self):
        spec = model.Fixed(16)
        assert spec.count == 16

    def test_from_arg_carries_an_index_and_a_divisor(self):
        """The entire lambda space in the friendly layer is an index and a divisor."""
        spec = model.FromArg(argument=1, divisor=4)
        assert spec.argument == 1
        assert spec.divisor == 4

    def test_from_arg_divisor_defaults_to_one(self):
        assert model.FromArg(argument=0).divisor == 1

    def test_glget_table_names_the_pname_argument(self):
        spec = model.GLGetTable(pname_argument=0)
        assert spec.pname_argument == 0

    def test_specs_compare_by_value(self):
        assert model.Fixed(4) == model.Fixed(4)
        assert model.Fixed(4) != model.Fixed(8)


class TestParameter:
    def test_defaults_are_a_plain_input(self):
        parameter = make_parameter()
        assert parameter.direction == model.IN
        assert parameter.size is model.NO_SIZE
        assert parameter.retain is False

    def test_an_array_parameter_knows_its_element_type(self):
        parameter = make_parameter(declaration='const GLfloat *')
        assert parameter.is_array
        assert parameter.element.buffer_format == 'f'

    def test_a_scalar_parameter_is_not_an_array(self):
        parameter = make_parameter(name='count', declaration='GLsizei')
        assert not parameter.is_array
        assert parameter.macro == 'GL_I'

    def test_a_void_pointer_is_an_untyped_array(self):
        """``const void *`` accepts any buffer, so it has no format to match."""
        parameter = make_parameter(name='pixels', declaration='const void *')
        assert parameter.is_array
        assert parameter.element.buffer_format == ''

    def test_output_parameters_are_returned_not_passed(self):
        parameter = make_parameter(
            name='params', declaration='GLint *', direction=model.OUT
        )
        assert parameter.direction == model.OUT
        assert parameter.is_output

    def test_retained_parameters_outlive_the_call(self):
        parameter = make_parameter(name='pointer', declaration='const void *', retain=True)
        assert parameter.retain


class TestCommand:
    def test_carries_its_registry_facts(self):
        command = model.Command(
            name='glBindTexture',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('target', 'GLenum'),
                make_parameter('texture', 'GLuint'),
            ],
        )
        assert command.name == 'glBindTexture'
        assert command.arg_names == ['target', 'texture']
        assert command.returns_void

    def test_pass_through_when_nothing_is_annotated(self):
        """Tier 1: 2,135 commands have no customisation at all."""
        command = model.Command(
            name='glBindTexture',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('target', 'GLenum'),
                make_parameter('texture', 'GLuint'),
            ],
        )
        assert command.tier == 1

    def test_declarative_annotations_are_tier_2(self):
        command = model.Command(
            name='glGenTextures',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('n', 'GLsizei'),
                make_parameter(
                    'textures',
                    'GLuint *',
                    direction=model.OUT,
                    size=model.FromArg(argument=0),
                ),
            ],
        )
        assert command.tier == 2

    def test_a_hand_written_body_is_tier_3(self):
        command = model.Command(
            name='glShaderSource',
            return_type=parse_type('void'),
            parameters=[make_parameter('shader', 'GLuint')],
            helper='string_array',
        )
        assert command.tier == 3

    def test_python_signature_drops_arguments_the_layer_computes(self):
        """``glGenTextures(n)`` — the output array is returned, not passed."""
        command = model.Command(
            name='glGenTextures',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('n', 'GLsizei'),
                make_parameter(
                    'textures',
                    'GLuint *',
                    direction=model.OUT,
                    size=model.FromArg(argument=0),
                ),
            ],
        )
        assert command.python_arguments == ['n', 'textures']
        assert command.required_arguments == ['n']

    def test_the_stub_name_is_derived_from_the_command_name(self):
        command = model.Command(
            name='glBindTexture', return_type=parse_type('void'), parameters=[]
        )
        assert command.stub_name == 'pygl_glBindTexture'

    def test_arrays_are_counted_for_the_cleanup_frame(self):
        command = model.Command(
            name='glPrioritizeTextures',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('n', 'GLsizei'),
                make_parameter('textures', 'const GLuint *'),
                make_parameter('priorities', 'const GLclampf *'),
            ],
        )
        assert command.array_count == 2

    def test_commands_with_no_arrays_need_no_frame(self):
        command = model.Command(
            name='glBindTexture',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('target', 'GLenum'),
                make_parameter('texture', 'GLuint'),
            ],
        )
        assert command.array_count == 0


class TestSignatureLine:
    """Phase 8: buildable from the command record alone, no external source."""

    def test_void_return(self):
        command = model.Command(
            name='glBindTexture',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('target', 'GLenum'),
                make_parameter('texture', 'GLuint'),
            ],
        )
        assert command.signature_line() == 'glBindTexture(target, texture) -> None'

    def test_output_parameter_becomes_the_return(self):
        command = model.Command(
            name='glGenTextures',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('n', 'GLsizei'),
                make_parameter(
                    'textures',
                    'GLuint *',
                    direction=model.OUT,
                    size=model.FromArg(argument=0),
                ),
            ],
        )
        assert command.signature_line() == 'glGenTextures(n) -> textures'

    def test_text_signature_is_a_valid_python_signature(self):
        command = model.Command(
            name='glGenTextures',
            return_type=parse_type('void'),
            parameters=[
                make_parameter('n', 'GLsizei'),
                make_parameter(
                    'textures',
                    'GLuint *',
                    direction=model.OUT,
                    size=model.FromArg(argument=0),
                ),
            ],
        )
        assert command.text_signature() == '($module, n, textures=None, /)'


def test_reserved_words_are_not_emitted_as_c_identifiers():
    """Registry parameter names collide with C keywords in a handful of places."""
    parameter = make_parameter(name='near', declaration='GLdouble')
    assert parameter.c_name != 'near'
    assert parameter.name == 'near'
