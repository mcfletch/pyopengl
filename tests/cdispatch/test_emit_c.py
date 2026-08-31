"""The C the generator emits for a command record."""

import pytest

from cdispatch import emit_c, model
from cdispatch.ctypes_model import parse_type


def command(name='glBindTexture', return_type='void', parameters=(), **kwargs):
    kwargs.setdefault('api', 'GL')
    return model.Command(
        name=name,
        return_type=parse_type(return_type),
        parameters=[
            model.Parameter(name=n, ctype=parse_type(t), **extra)
            for n, t, extra in parameters
        ],
        **kwargs,
    )


def body(command):
    return emit_c.emit_stub(command)


class TestPassThrough:
    def test_scalar_call(self):
        text = body(
            command(parameters=[('target', 'GLenum', {}), ('texture', 'GLuint', {})])
        )
        assert 'PYGL_ARITY(2);' in text
        assert 'PYGL_U(0, target);' in text
        assert 'PYGL_U(1, texture);' in text
        assert 'PYGL_CONV_OK();' in text
        assert 'PYGL_CALL_V((unsigned int, unsigned int), (target, texture));' in text
        assert 'Py_RETURN_NONE;' in text
        assert '_fail:' in text

    def test_no_argument_call(self):
        text = body(command(name='glEnd'))
        assert 'PYGL_ARITY(0);' in text
        assert 'PYGL_CALL_V((void), ());' in text

    def test_float_and_double_arguments_use_their_own_macros(self):
        text = body(
            command(
                name='glDepthRange',
                parameters=[('near', 'GLdouble', {}), ('far', 'GLdouble', {})],
            )
        )
        assert 'PYGL_D(0, _near);' in text
        assert 'PYGL_D(1, _far);' in text
        assert 'PYGL_CALL_V((double, double), (_near, _far));' in text

    def test_integer_return(self):
        text = body(
            command(
                name='glIsTexture',
                return_type='GLboolean',
                parameters=[('texture', 'GLuint', {})],
            )
        )
        assert 'PYGL_CALL_R(_result, unsigned char,' in text
        assert 'PyLong_FromLong' in text

    def test_string_return_is_bytes(self):
        text = body(
            command(
                name='glGetString',
                return_type='const GLubyte *',
                parameters=[('name', 'GLenum', {})],
            )
        )
        assert 'pygl_bytes_or_none' in text


class TestArrays:
    def test_input_array_takes_a_frame_slot(self):
        text = body(
            command(
                name='glUniformMatrix4fv',
                parameters=[
                    ('location', 'GLint', {}),
                    ('count', 'GLsizei', {}),
                    ('transpose', 'GLboolean', {}),
                    ('value', 'const GLfloat *', {}),
                ],
            )
        )
        assert 'PYGL_FRAME(1);' in text
        assert 'PYGL_ARRAY_IN(3, value, &pygl_elem_GLfloat);' in text
        assert 'PYGL_CLEANUP();' in text

    def test_two_arrays_share_one_cleanup_path(self):
        """The frame exists so that a later failure releases an earlier buffer."""
        text = body(
            command(
                name='glPrioritizeTextures',
                parameters=[
                    ('n', 'GLsizei', {}),
                    ('textures', 'const GLuint *', {}),
                    ('priorities', 'const GLclampf *', {}),
                ],
            )
        )
        assert 'PYGL_FRAME(2);' in text
        assert text.count('PYGL_CLEANUP();') == 2
        assert text.count('_fail:') == 1

    def test_scalars_are_converted_before_arrays_are_acquired(self):
        """Nothing needs unwinding while only scalars have been converted."""
        text = body(
            command(
                name='glUniformMatrix4fv',
                parameters=[
                    ('location', 'GLint', {}),
                    ('value', 'const GLfloat *', {}),
                    ('count', 'GLsizei', {}),
                ],
            )
        )
        assert text.index('PYGL_CONV_OK();') < text.index('PYGL_ARRAY_IN')
        assert text.index('PYGL_I(0, location);') < text.index('PYGL_CONV_OK();')
        assert text.index('PYGL_SZ(2, count);') < text.index('PYGL_CONV_OK();')

    def test_fixed_size_input_arrays_are_checked(self):
        text = body(
            command(
                name='glIndexubv',
                parameters=[('c', 'const GLubyte *', {'size': model.Fixed(1)})],
            )
        )
        assert 'PYGL_ARRAY_IN_SIZED(0, c, &pygl_elem_GLubyte, 1);' in text

    def test_void_pointer_accepts_any_buffer(self):
        text = body(
            command(
                name='glDrawElements',
                parameters=[
                    ('mode', 'GLenum', {}),
                    ('count', 'GLsizei', {}),
                    ('type', 'GLenum', {}),
                    ('indices', 'const void *', {}),
                ],
            )
        )
        assert 'PYGL_ARRAY_IN(3, indices, &pygl_elem_any);' in text


class TestOutputs:
    def test_output_sized_from_another_argument(self):
        text = body(
            command(
                name='glGenTextures',
                parameters=[
                    ('n', 'GLsizei', {}),
                    (
                        'textures',
                        'GLuint *',
                        {'direction': model.OUT, 'size': model.FromArg(argument=0)},
                    ),
                ],
            )
        )
        assert 'PYGL_ARITY_RANGE(1, 2);' in text
        assert 'PYGL_ARRAY_OUT(1, textures, &pygl_elem_GLuint, (Py_ssize_t)(n));' in text
        assert 'pygl_output_value' in text

    def test_output_with_a_divisor(self):
        text = body(
            command(
                name='glGetUniformfv',
                parameters=[
                    ('location', 'GLint', {}),
                    (
                        'params',
                        'GLfloat *',
                        {
                            'direction': model.OUT,
                            'size': model.FromArg(argument=0, divisor=4),
                        },
                    ),
                ],
            )
        )
        assert '(Py_ssize_t)(location / 4)' in text

    def test_constant_size_output(self):
        text = body(
            command(
                name='glGetActiveAttribLength',
                parameters=[
                    ('program', 'GLuint', {}),
                    (
                        'length',
                        'GLsizei *',
                        {'direction': model.OUT, 'size': model.Fixed(1)},
                    ),
                ],
            )
        )
        assert 'PYGL_ARRAY_OUT(1, length, &pygl_elem_GLsizei, (Py_ssize_t)(1));' in text


class TestSelection:
    """Only commands whose whole annotation set the C implements are emitted.

    A command the C claimed but implemented only partly would silently lose the
    friendly behaviour the Python wrapper provides, which is the one failure
    mode the staging is designed to make impossible.
    """

    def test_tier_one_is_emitted(self):
        assert emit_c.is_emittable(
            command(parameters=[('target', 'GLenum', {}), ('texture', 'GLuint', {})])
        )

    def test_a_hand_written_entry_point_is_emitted(self):
        """glShaderSource has a C function of its own, so it is claimed."""
        assert emit_c.is_emittable(command(name='glShaderSource', api='GL'))
        assert emit_c.hand_written(command(name='glShaderSource', api='GL'))

    def test_a_family_with_no_hand_written_body_is_not_emitted(self):
        assert not emit_c.is_emittable(command(name='glTexImage2D', helper='image'))

    def test_image_sized_outputs_are_not_emitted_yet(self):
        """An image's size depends on the current pixel-store state."""
        assert not emit_c.is_emittable(
            command(
                name='glReadPixels',
                parameters=[
                    ('format', 'GLenum', {}),
                    ('type', 'GLenum', {}),
                    (
                        'pixels',
                        'void *',
                        {
                            'direction': model.OUT,
                            'size': model.ImageSize(
                                format_argument=0, type_argument=1
                            ),
                        },
                    ),
                ],
            )
        )

    def test_struct_pointer_returns_are_not_emitted_yet(self):
        """The GLX queries hand back ctypes pointers to X structures."""
        assert not emit_c.is_emittable(
            command(name='glXGetVisualFromFBConfig', return_type='XVisualInfo *')
        )

    def test_string_returns_are_emitted(self):
        assert emit_c.is_emittable(
            command(
                name='glGetString',
                return_type='const GLubyte *',
                parameters=[('name', 'GLenum', {})],
            )
        )


def test_void_pointer_output_is_a_ubyte_array():
    """``wrapper.setOutput`` maps a ``void *`` output to ``GLubyteArray``.

    Without it a caller's wrongly-typed output array is accepted as any
    contiguous buffer rather than being coerced -- and the coercion is what
    tells the caller their result would have been lost.
    """
    text = body(
        command(
            name='glGetBufferSubData',
            parameters=[
                ('target', 'GLenum', {}),
                ('offset', 'GLintptr', {}),
                ('size', 'GLsizeiptr', {}),
                (
                    'data',
                    'void *',
                    {'direction': model.OUT, 'size': model.FromArg(argument=2)},
                ),
            ],
        )
    )
    assert 'PYGL_ARRAY_OUT(3, data, &pygl_elem_GLubyte,' in text


def test_void_pointer_input_still_accepts_any_buffer():
    text = body(
        command(
            name='glBufferData',
            parameters=[
                ('target', 'GLenum', {}),
                ('size', 'GLsizeiptr', {}),
                ('data', 'const void *', {}),
                ('usage', 'GLenum', {}),
            ],
        )
    )
    assert 'PYGL_ARRAY_IN(2, data, &pygl_elem_any);' in text


def test_pointer_array_output_uses_the_voidp_array_type():
    """``void **`` outputs allocate through GLvoidpArray, as setOutput does.

    The generic ArrayDatatype cannot size an allocation, so an output that
    named it would allocate too little and the GL would write past the end.
    """
    text = body(
        command(
            name='glGetVertexAttribPointerv',
            parameters=[
                ('index', 'GLuint', {}),
                ('pname', 'GLenum', {}),
                (
                    'pointer',
                    'void **',
                    {'direction': model.OUT, 'size': model.Fixed(1)},
                ),
            ],
        )
    )
    assert 'PYGL_ARRAY_OUT(2, pointer, &pygl_elem_voidp, (Py_ssize_t)(1));' in text


class TestGLGetSizedOutputs:
    """Phase 4's second half: outputs whose size comes from the pname table."""

    def glgetv(self):
        return command(
            name='glGetIntegerv',
            api='GL',
            parameters=[
                ('pname', 'GLenum', {}),
                (
                    'params',
                    'GLint *',
                    {
                        'direction': model.OUT,
                        'size': model.GLGetTable(pname_argument=0),
                    },
                ),
            ],
        )

    def test_is_emitted(self):
        assert emit_c.is_emittable(self.glgetv())

    def test_names_the_pname_argument_and_the_api_table(self):
        text = body(self.glgetv())
        assert (
            'PYGL_ARRAY_OUT_GLGET(1, params, &pygl_elem_GLint, pname, '
            'pygl_glget_GL);' in text
        )

    def test_the_element_count_comes_from_the_lookup(self):
        """The count is not known until the table is consulted at run time."""
        text = body(self.glgetv())
        assert 'params_count' in text
        assert 'pygl_output_value(&_bufs[params_slot], &pygl_elem_GLint, params_count)' in text


class TestMultipleOutputs:
    """Several outputs compose into a tuple, in the order they were declared."""

    def two_outputs(self):
        return command(
            name='glGetQueryObjectuiv',
            parameters=[
                ('id', 'GLuint', {}),
                (
                    'first',
                    'GLint *',
                    {'direction': model.OUT, 'size': model.Fixed(1)},
                ),
                (
                    'second',
                    'GLuint *',
                    {'direction': model.OUT, 'size': model.Fixed(4)},
                ),
            ],
        )

    def test_is_emitted(self):
        assert emit_c.is_emittable(self.two_outputs())

    def test_both_outputs_get_a_frame_slot(self):
        text = body(self.two_outputs())
        assert 'PYGL_FRAME(2);' in text
        assert 'PYGL_ARRAY_OUT(1, first,' in text
        assert 'PYGL_ARRAY_OUT(2, second,' in text

    def test_the_arity_range_covers_both(self):
        assert 'PYGL_ARITY_RANGE(1, 3);' in body(self.two_outputs())

    def test_a_tuple_is_built_from_them(self):
        text = body(self.two_outputs())
        assert 'pygl_output_tuple' in text
        assert '_outputs[] = {' in text


class TestPointerReturns:
    def test_a_void_pointer_return_is_an_address(self):
        """``glMapBuffer`` hands back an int today, and None for a null."""
        text = body(command(name='glMapBuffer', return_type='void *'))
        assert 'pygl_address_or_none' in text

    def test_a_void_pointer_return_is_emitted(self):
        assert emit_c.is_emittable(command(name='glMapBuffer', return_type='void *'))

    def test_a_struct_pointer_return_is_not(self):
        """``glXChooseVisual`` hands back a ctypes pointer to a struct."""
        assert not emit_c.is_emittable(
            command(name='glXChooseVisual', return_type='XVisualInfo *')
        )


class TestOutputPosition:
    """An output that is not a trailing argument cannot be optional.

    ``glGetPerfMonitorGroupsAMD(numGroups, groupsSize, groups)`` has outputs at
    positions 0 and 2, so there is no arity at which "the caller omitted the
    output" is unambiguous -- omitting it would shift the next argument into
    its place.  Five commands are shaped this way and they stay on ctypes.
    """

    def leading_output(self):
        return command(
            name='glGetPerfMonitorGroupsAMD',
            parameters=[
                (
                    'numGroups',
                    'GLint *',
                    {'direction': model.OUT, 'size': model.Fixed(1)},
                ),
                ('groupsSize', 'GLsizei', {}),
                (
                    'groups',
                    'GLuint *',
                    {'direction': model.OUT, 'size': model.FromArg(argument=1)},
                ),
            ],
        )

    def test_is_not_emitted(self):
        assert not emit_c.is_emittable(self.leading_output())

    def test_the_reason_is_stated(self):
        assert 'trailing' in emit_c.exclusion_reason(self.leading_output())

    def test_trailing_outputs_are_still_emitted(self):
        assert emit_c.is_emittable(
            command(
                name='glGenTextures',
                parameters=[
                    ('n', 'GLsizei', {}),
                    (
                        'textures',
                        'GLuint *',
                        {'direction': model.OUT, 'size': model.FromArg(argument=0)},
                    ),
                ],
            )
        )
