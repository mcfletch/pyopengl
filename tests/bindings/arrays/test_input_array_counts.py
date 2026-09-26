"""An input array read ``count`` times over is measured against the count.

``glViewportArrayv(first, count, v)`` reads four floats per viewport from
``v``, and nothing in the call ties the array to the count: an array shorter
than ``count * 4`` has the driver read past the end of the caller's buffer.
The annotation table records the size as ``from-argument`` with a
``multiplier``, and both implementations of the entry points refuse a short
array before the call.

A longer array is accepted.  The GL reads ``count`` items and no more, and a
caller updating the first few entries of a larger array is ordinary.

An array of strings is measured the same way.  ``glGetUniformIndices(program,
uniformCount, uniformNames, uniformIndices)`` reads ``uniformCount`` pointers
from ``uniformNames``, so fewer strings than that, or ``None`` for a positive
count, has the driver read past the array or from address zero.  A
``GLchar *const *`` the caller built is passed as it is, since only its builder
knows its length.

The refusal happens before a function pointer is resolved, so these run with no
context and cover the GLES2 and vendor entry points a desktop driver does not
offer.  ``tests/gl/test_gl41.py`` drives the core ones against a real context.
"""

import pytest

from OpenGL import _configflags, _declarations
from OpenGL._dispatch import entry_points

np = pytest.importorskip('numpy')

pytestmark = pytest.mark.skipif(
    not _configflags.ARRAY_SIZE_CHECKING,
    reason='ARRAY_SIZE_CHECKING is off, so a short array is not refused',
)

#: ``(declaring module, entry point, values per item, element type)``
FAMILY = [
    ('OpenGL.raw.GL.ARB.viewport_array', 'glViewportArrayv', 4, 'f'),
    ('OpenGL.raw.GL.ARB.viewport_array', 'glScissorArrayv', 4, 'i'),
    ('OpenGL.raw.GL.ARB.viewport_array', 'glDepthRangeArrayv', 2, 'd'),
    ('OpenGL.raw.GL.ARB.viewport_array', 'glDepthRangeArraydvNV', 2, 'd'),
    ('OpenGL.raw.GL.NVX.gpu_multicast2', 'glMulticastViewportArrayvNVX', 4, 'f'),
    ('OpenGL.raw.GL.NVX.gpu_multicast2', 'glMulticastScissorArrayvNVX', 4, 'i'),
    ('OpenGL.raw.GL.NV.scissor_exclusive', 'glScissorExclusiveArrayvNV', 4, 'i'),
    ('OpenGL.raw.GLES2.NV.scissor_exclusive', 'glScissorExclusiveArrayvNV', 4, 'i'),
    ('OpenGL.raw.GLES2.NV.viewport_array', 'glViewportArrayvNV', 4, 'f'),
    ('OpenGL.raw.GLES2.NV.viewport_array', 'glScissorArrayvNV', 4, 'i'),
    ('OpenGL.raw.GLES2.NV.viewport_array', 'glDepthRangeArrayfvNV', 2, 'f'),
    ('OpenGL.raw.GLES2.OES.viewport_array', 'glViewportArrayvOES', 4, 'f'),
    ('OpenGL.raw.GLES2.OES.viewport_array', 'glScissorArrayvOES', 4, 'i'),
    ('OpenGL.raw.GLES2.OES.viewport_array', 'glDepthRangeArrayfvOES', 2, 'f'),
]

IDS = [
    '%s.%s' % (_declarations.api_of(module), name)
    for module, name, _per, _dtype in FAMILY
]


def ctypes_wrapper(module, name):
    """The entry point the ctypes path builds, from the declaration and table."""
    return _declarations.ctypes_entry_point(module, name)


def c_entry_point(module, name):
    """The C entry point, with the layer installed if nothing has yet."""
    from OpenGL import dispatch

    if dispatch.settle() != 'c':
        pytest.skip('the C dispatch layer is not running: %s' % (dispatch.status().reason,))
    return entry_points[(_declarations.api_of(module), name)]


def leading(name, count):
    """The scalar arguments before ``v``: ``gpu`` for the multicast pair."""
    return (0, 0, count) if 'Multicast' in name else (0, count)


IMPLEMENTATIONS = pytest.mark.parametrize(
    'implementation', [ctypes_wrapper, c_entry_point], ids=['ctypes', 'c']
)


class TestTheTableStatesTheSize:
    @pytest.mark.parametrize('module,name,per,dtype', FAMILY, ids=IDS)
    def test_the_size_is_a_multiple_of_the_count(self, module, name, per, dtype):
        api = _declarations.api_of(module)
        bits = _declarations.annotations()['%s.%s' % (api, name)]['parameters']['v']
        assert bits['array'] is True
        assert bits['size'] == {
            'kind': 'from-argument',
            'argument': 'count',
            'divisor': 1,
            'multiplier': per,
        }


@IMPLEMENTATIONS
class TestAShortArrayIsRefused:
    @pytest.mark.parametrize('module,name,per,dtype', FAMILY, ids=IDS)
    def test_one_item_short(self, implementation, module, name, per, dtype):
        function = implementation(module, name)
        with pytest.raises(ValueError):
            function(*leading(name, 2), np.zeros(per, dtype))

    @pytest.mark.parametrize('module,name,per,dtype', FAMILY, ids=IDS)
    def test_one_value_short(self, implementation, module, name, per, dtype):
        function = implementation(module, name)
        with pytest.raises(ValueError):
            function(*leading(name, 3), np.zeros(3 * per - 1, dtype))

    @pytest.mark.parametrize('module,name,per,dtype', FAMILY, ids=IDS)
    def test_empty(self, implementation, module, name, per, dtype):
        """An empty array converts to a null data pointer, which is not a
        null argument: the driver would read ``count`` items from address
        zero."""
        function = implementation(module, name)
        with pytest.raises(ValueError):
            function(*leading(name, 1), np.zeros(0, dtype))

    def test_none_is_a_null_pointer_the_driver_would_read(self, implementation):
        function = implementation('OpenGL.raw.GL.ARB.viewport_array', 'glViewportArrayv')
        with pytest.raises(ValueError):
            function(0, 1, None)

    def test_the_message_gives_both_lengths(self, implementation):
        function = implementation('OpenGL.raw.GL.ARB.viewport_array', 'glViewportArrayv')
        with pytest.raises(ValueError, match='at least 32 byte'):
            function(0, 2, np.zeros(4, 'f'))


#: ``(declaring module, entry point, string-array parameter, count parameter,
#: the call's arguments around the two)``.  ``glShaderSource`` is not here: its
#: friendly form takes the strings alone and counts them itself.
STRINGS = [
    ('OpenGL.raw.GL.ARB.shading_language_include', 'glCompileShaderIncludeARB',
     'path', 'count', ((0,), (None,))),
    ('OpenGL.raw.GL.VERSION.GL_4_1', 'glCreateShaderProgramv',
     'strings', 'count', ((0,), ())),
    ('OpenGL.raw.GL.EXT.separate_shader_objects', 'glCreateShaderProgramvEXT',
     'strings', 'count', ((0,), ())),
    ('OpenGL.raw.GL.VERSION.GL_3_1', 'glGetUniformIndices',
     'uniformNames', 'uniformCount', ((0,), ())),
    ('OpenGL.raw.GL.VERSION.GL_3_0', 'glTransformFeedbackVaryings',
     'varyings', 'count', ((0,), (0,))),
    ('OpenGL.raw.GL.EXT.transform_feedback', 'glTransformFeedbackVaryingsEXT',
     'varyings', 'count', ((0,), (0,))),
    ('OpenGL.raw.GLES2.EXT.separate_shader_objects', 'glCreateShaderProgramvEXT',
     'strings', 'count', ((0,), ())),
    ('OpenGL.raw.GLES3.VERSION.GLES3_3_1', 'glCreateShaderProgramv',
     'strings', 'count', ((0,), ())),
    ('OpenGL.raw.GLES3.VERSION.GLES3_3_0', 'glGetUniformIndices',
     'uniformNames', 'uniformCount', ((0,), ())),
    ('OpenGL.raw.GLES3.VERSION.GLES3_3_0', 'glTransformFeedbackVaryings',
     'varyings', 'count', ((0,), (0,))),
]

STRING_IDS = [
    '%s.%s' % (_declarations.api_of(module), name)
    for module, name, _parameter, _count, _around in STRINGS
]


def string_call(function, around, count, strings):
    before, after = around
    return function(*before, count, strings, *after)


class TestTheTableStatesTheStringCount:
    @pytest.mark.parametrize(
        'module,name,parameter,count,around', STRINGS, ids=STRING_IDS
    )
    def test_the_count_is_an_argument(self, module, name, parameter, count, around):
        api = _declarations.api_of(module)
        bits = _declarations.annotations()['%s.%s' % (api, name)]['parameters'][
            parameter
        ]
        assert bits['size'] == {
            'kind': 'from-argument',
            'argument': count,
            'divisor': 1,
            'multiplier': 1,
        }


@IMPLEMENTATIONS
class TestTooFewStringsAreRefused:
    @pytest.mark.parametrize(
        'module,name,parameter,count,around', STRINGS, ids=STRING_IDS
    )
    def test_one_string_short(
        self, implementation, module, name, parameter, count, around
    ):
        function = implementation(module, name)
        with pytest.raises(ValueError, match='at least 2 strings, got 1'):
            string_call(function, around, 2, ['only'])

    @pytest.mark.parametrize(
        'module,name,parameter,count,around', STRINGS, ids=STRING_IDS
    )
    def test_none_for_a_positive_count(
        self, implementation, module, name, parameter, count, around
    ):
        """A null ``char **`` the driver would read ``count`` pointers from."""
        function = implementation(module, name)
        with pytest.raises(ValueError, match='at least 3 strings, got None'):
            string_call(function, around, 3, None)


@IMPLEMENTATIONS
class TestTheMessagesAgree:
    def test_none_is_named_as_none(self, implementation):
        function = implementation('OpenGL.raw.GL.ARB.viewport_array', 'glViewportArrayv')
        with pytest.raises(ValueError, match='at least 16 byte array, got None'):
            function(0, 1, None)


class TestAnOutputSizedFromAnArgument:
    """The ctypes path allocates what the C allocates: ``count * multiplier / divisor``."""

    @pytest.mark.parametrize(
        'divisor,multiplier,count,expected',
        [(1, 1, 6, 6), (4, 1, 8, 2), (1, 4, 3, 12), (2, 3, 4, 6)],
    )
    def test_the_length_scales_both_ways(self, divisor, multiplier, count, expected):
        assert _declarations._scaled_by(divisor, multiplier)(count) == (expected,)
