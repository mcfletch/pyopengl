"""Arrays of pointer-sized integers, which several entry points take.

``GLintptr`` is a whole element type in the API -- buffer offsets
(``glBindVertexBuffers``), and VDPAU surface handles under the alias
``GLvdpauSurfaceNV`` -- and an argument declared ``const GLintptr *`` is an
array like any other. With no datatype for it the ctypes path has nothing to
convert with, and hands a numpy array straight to ctypes, which refuses it:

    ctypes.ArgumentError: argument 2: expected LP_c_long instance instead of
    numpy.ndarray

``GLint64Array`` is not the same thing. It is fixed at 64 bits, while
``GLintptr`` is the width of a pointer -- equal on a 64-bit build and wrong on a
32-bit one.
"""

import ctypes

import pytest

from OpenGL import _configflags

from OpenGL import arrays
from OpenGL.raw.GL import _types

np = pytest.importorskip('numpy')


#: For the cases whose subject *is* the conversion PyOpenGL performs on the way
#: in.  ``ERROR_ON_COPY`` is a caller refusing exactly that, so under it there
#: is nothing here to assert.
converts_by_copying = pytest.mark.skipif(
    _configflags.ERROR_ON_COPY,
    reason='ERROR_ON_COPY refuses the conversion this case is about',
)


class TestTheDatatypeExists:
    def test_the_package_offers_it(self):
        assert arrays.GLintptrArray is not None

    def test_its_element_is_the_pointer_sized_integer(self):
        assert arrays.GLintptrArray.baseType is _types.GLintptr

    def test_that_is_as_wide_as_a_pointer(self):
        """Which is the whole reason it is not GLint64Array."""
        assert ctypes.sizeof(_types.GLintptr) == ctypes.sizeof(ctypes.c_void_p)

    def test_a_vdpau_surface_is_one_of_them(self):
        """``GLvdpauSurfaceNV`` is an alias for ``GLintptr``, so the handles
        VDPAU deals in are arrays of this."""
        assert _types.GLvdpauSurfaceNV is _types.GLintptr


class TestConvertingAnArray:
    def test_a_matching_array_keeps_its_values(self):
        values = np.array([1, 2, 3], dtype='intp')
        converted = arrays.GLintptrArray.asArray(values)
        assert arrays.GLintptrArray.arraySize(converted) == 3

    def test_it_counts_the_bytes_a_pointer_wide_element_occupies(self):
        values = np.array([1, 2, 3], dtype='intp')
        converted = arrays.GLintptrArray.asArray(values)
        assert (arrays.GLintptrArray.arrayByteCount(converted)
                == 3 * ctypes.sizeof(_types.GLintptr))

    @converts_by_copying
    def test_a_list_converts_too(self):
        """A list of handles is what a great deal of calling code passes."""
        converted = arrays.GLintptrArray.asArray([4, 5])
        assert arrays.GLintptrArray.arraySize(converted) == 2

    @converts_by_copying
    def test_a_narrower_array_is_converted_rather_than_reinterpreted(self):
        converted = arrays.GLintptrArray.asArray(np.array([7, 8], dtype='int32'))
        assert (arrays.GLintptrArray.arrayByteCount(converted)
                == 2 * ctypes.sizeof(_types.GLintptr))


class TestAPointerArgumentGetsItsConversion:
    """``setInputArraySize`` is asked for these conversions by the annotation
    table -- ``{'offsets': {'array': True}}`` -- and has to find an array type
    for the declared pointer to make one.

    Its escape hatch for a pointer *to a pointer* has to distinguish one from a
    pointer to a simple type, and testing for a ``_type_`` attribute does not:
    a simple ctypes type carries one of its own, the struct format character,
    ``'l'`` for a ``c_long``. Matching there costs no exception and no
    converter -- the array reaches ctypes as it stands and is refused.
    """

    def _wrapped(self, argtype):
        from OpenGL import wrapper

        class Stub:
            __name__ = 'glStub'
            argNames = ('count', 'values')
            argtypes = (ctypes.c_uint, argtype)
            restype = None

            def __call__(self, *args):        # pragma: no cover - never called
                return None

        return wrapper.wrapper(Stub()).setInputArraySize('values', None)

    @converts_by_copying
    def test_a_pointer_to_a_pointer_sized_integer_is_converted(self):
        built = self._wrapped(ctypes.POINTER(_types.GLintptr))
        assert built.pyConverters is not None
        assert built.pyConverters[1] is not None

    @converts_by_copying
    def test_so_is_one_the_datatype_already_existed_for(self):
        """The same escape swallowed these too; only nobody had noticed,
        because the declarations name an array type for most of them."""
        built = self._wrapped(ctypes.POINTER(_types.GLint))
        assert built.pyConverters[1] is not None

    def test_a_pointer_to_a_pointer_still_takes_the_escape(self):
        """What the branch was for: an array of string pointers has no single
        element type to convert to."""
        from OpenGL import wrapper

        built = self._wrapped(ctypes.POINTER(ctypes.POINTER(_types.GLchar)))
        assert isinstance(built, wrapper.Wrapper)
        assert 'pyConverters' not in built.__dict__

    @converts_by_copying
    def test_a_type_with_no_array_datatype_says_so(self):
        """Rather than passing it through unconverted, which is what made this
        invisible.

        The guard belongs to the converting implementation.  ``ERROR_ON_COPY``
        selects a second ``setInputArraySize`` that installs no converter at
        all unless a size was given, so there is nothing there to refuse an
        unconvertible declaration -- which is the flag doing what it says
        rather than a gap to assert against.
        """
        with pytest.raises(TypeError, match='array'):
            self._wrapped(ctypes.POINTER(ctypes.c_wchar))
