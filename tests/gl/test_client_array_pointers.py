#! /usr/bin/env python3
"""The GL reads each client array from memory holding the values passed in.

``glColorPointerf(array)`` and its siblings in ``OpenGL.GL.pointers`` convert
the array to their element type and hand the GL its address.  The address the
driver stores is read back with ``glGetPointerv`` and the bytes there compared
with the array: a conversion to the wrong type still yields an address, and a
draw from it produces garbage rather than an error.

The typed setters are derived from the same entry points as the untyped ones,
so each is checked on its own, and so is the untyped entry point once the typed
ones have been built from it.

The element type is the setter's rather than the caller's, so an array of
another type is converted.  ``ERROR_ON_COPY`` is a caller refusing that
conversion, and there it is a ``CopyError`` instead: the pairs of cases below
say which run is which.
"""

import ctypes

import pytest

np = pytest.importorskip('numpy')

from gltestcase import GLTestCase  # noqa: E402
from OpenGL import _configflags  # noqa: E402
from OpenGL.arrays import arraydatatype  # noqa: E402
from OpenGL.error import CopyError  # noqa: E402
from OpenGL.GL import pointers  # noqa: E402
from OpenGL.GL import *  # noqa: F401,F403,E402
from OpenGL.raw.GL.VERSION import GL_1_1 as raw  # noqa: E402

#: The flag is fixed when the wrappers are built, and ``_configflags`` holds
#: the value they were built with.
converts = pytest.mark.skipif(
    _configflags.ERROR_ON_COPY,
    reason='ERROR_ON_COPY refuses the conversion this case is about',
)
refuses_the_copy = pytest.mark.skipif(
    not _configflags.ERROR_ON_COPY,
    reason='the conversion this case expects to be refused is made here',
)

#: name -> (element type, the array state's pointer query, components per element)
TYPED_SETTERS = {
    name: (gl_type, query, default_size or 1)
    for name, _base, gl_type, query, _start, default_size in pointers.POINTER_FUNCTION_DATA
}


def element_dtype(gl_type):
    """The numpy dtype a typed setter converts its array to."""
    return np.dtype(arraydatatype.GL_CONSTANT_TO_ARRAY_TYPE[gl_type].baseType)


def values_for(gl_type, size):
    """Four elements of distinct, exactly representable values."""
    dtype = element_dtype(gl_type)
    count = 4 * size
    if dtype.kind == 'f':
        values = np.arange(count, dtype='d') / 8.0 + 0.125
    else:
        values = np.arange(count) % 100 + 1
    return np.array(values.reshape(4, size), dtype=dtype)


def driver_bytes(query, length):
    """``length`` bytes from the address the driver holds for ``query``."""
    address = ctypes.c_void_p()
    raw.glGetPointerv(query, ctypes.byref(address))
    assert address.value, 'the driver holds no pointer for %s' % (query,)
    return ctypes.string_at(address.value, length)


class TestTypedSetters(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_each_hands_the_driver_the_array_it_converted(self):
        for name, (gl_type, query, size) in sorted(TYPED_SETTERS.items()):
            with self.subTest(setter=name):
                data = values_for(gl_type, size)
                result = getattr(pointers, name)(data)
                assert np.asarray(result).dtype == element_dtype(gl_type)
                assert driver_bytes(query, data.nbytes) == data.tobytes()
        self.check_error('typed client-array setters')

    @converts
    def test_a_byte_setter_takes_signed_bytes(self):
        data = np.array([[-128, -1, 0], [1, 64, 127]], 'b')
        for name in ('glIndexPointerb', 'glTexCoordPointerb', 'glVertexPointerb'):
            with self.subTest(setter=name):
                gl_type, query, _size = TYPED_SETTERS[name]
                getattr(pointers, name)(data)
                expected = data.astype(element_dtype(gl_type))
                assert driver_bytes(query, expected.nbytes) == expected.tobytes()
        self.check_error('byte client-array setters')

    @refuses_the_copy
    def test_a_byte_setter_will_not_widen_where_copies_are_refused(self):
        """Widening the bytes to GL_INT is the copy the flag is set to find.

        The driver is told GL_INT whatever array the setter was handed, so
        passing the bytes through unwidened would have it read four times
        their length.
        """
        data = np.array([[-128, -1, 0], [1, 64, 127]], 'b')
        for name in ('glIndexPointerb', 'glTexCoordPointerb', 'glVertexPointerb'):
            with self.subTest(setter=name):
                with self.assertRaises(CopyError):
                    getattr(pointers, name)(data)
        self.check_error('byte client-array setters under ERROR_ON_COPY')

    def test_the_byte_setters_that_take_no_bytes_widen_alike(self):
        """glIndexPointer, glTexCoordPointer and glVertexPointer take no GL_BYTE."""
        widened = {
            TYPED_SETTERS[name][0]
            for name in ('glIndexPointerb', 'glTexCoordPointerb', 'glVertexPointerb')
        }
        assert widened == {GL_INT}

    @converts
    def test_a_float64_array_is_converted_to_the_setters_type(self):
        data = np.array([[0.15, 0.17, 0.2]] * 4, 'd')
        result = pointers.glColorPointerf(data)
        expected = data.astype('f')
        assert np.asarray(result).dtype == np.dtype('f')
        assert (
            driver_bytes(GL_COLOR_ARRAY_POINTER, expected.nbytes) == expected.tobytes()
        )

    @refuses_the_copy
    def test_a_float64_array_is_refused_where_copies_are_refused(self):
        data = np.array([[0.15, 0.17, 0.2]] * 4, 'd')
        with self.assertRaises(CopyError):
            pointers.glColorPointerf(data)


class TestDemotedUntypedSetter(GLTestCase):
    """What an untyped setter becomes when a client assigns ``errcheck``.

    Asked of what demotion installs rather than by demoting the live entry
    point, which would last for the rest of the process.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_it_converts_to_the_type_it_is_given(self):
        pytest.importorskip('OpenGL._dispatch')
        from OpenGL import dispatch as dispatch_api
        from OpenGL._dispatch import support

        if dispatch_api.settle() != 'c':  # pragma: no cover - depends on the axis
            pytest.skip('the C dispatch layer is not the implementation running')
        demoted = support.demoted_callable(pointers.glColorPointer)
        data = values_for(GL_FLOAT, 3)
        demoted(3, GL_FLOAT, 0, data)
        assert driver_bytes(GL_COLOR_ARRAY_POINTER, data.nbytes) == data.tobytes()
