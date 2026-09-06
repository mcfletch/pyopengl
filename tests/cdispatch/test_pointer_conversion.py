"""How a handle crosses between Python and the compiled dispatch layer.

Two conversions carry every opaque handle: :func:`support.as_pointer` turns
what a caller passed into the address the call is made with, and
:func:`support.opaque` turns the address a call answered with back into what
the ctypes path would have produced.  Both have to agree with ctypes, because
the two implementations are alternatives and a program must not be able to tell
which one it is on.

**WGL declares its handles differently from the rest.**  EGL's ``EGLDisplay``
and GL's ``GLsync`` are ctypes pointer classes; WGL's ``HDC``, ``HGLRC`` and
``HPBUFFERARB`` are pointer-*sized simple* types, deliberately so, since ctypes
shares every reference to ``c_void_p`` and a shared one would disable the array
machinery.  A conversion that recognises only pointer classes therefore reads a
WGL handle as an ordinary object and answers with the address of the wrapper --
a pointer into the interpreter's heap, handed to the display driver, with no
error anywhere to say so.

These are declaration-level questions, so they answer on any platform: a Linux
run holds the Windows path to the same contract.
"""

import ctypes

import pytest

from OpenGL._dispatch import support


def wgl_types():
    from OpenGL.raw.WGL import _types

    return _types


#: The handle types WGL declares as pointer-sized simple types.  Each names a
#: thing an offscreen renderer holds: the device context, the render context
#: and the pbuffer.
WGL_HANDLES = ('HDC', 'HGLRC', 'HPBUFFERARB')

#: A handle with its top half set.  Windows documents USER and GDI handles as
#: 32-bit values sign-extended to 64 bits, so roughly half of the real ones
#: look like this, and a conversion that keeps only the low half turns them
#: into a different, live handle rather than into an obvious zero.
WIDE = 0xFFFFFFFFE40111CC

#: One that fits in 32 bits, so a truncating conversion would pass this and
#: fail only the one above.  Both are checked for that reason.
NARROW = 0x00000000150109E4


class TestAHandleIsPassedByItsValue:
    """``as_pointer`` answers with the handle, not with where it is stored."""

    @pytest.mark.parametrize('name', WGL_HANDLES)
    @pytest.mark.parametrize('address', [NARROW, WIDE])
    def test_a_wgl_handle_converts_to_itself(self, name, address):
        handle = getattr(wgl_types(), name)(address)
        assert support.as_pointer(handle) == address

    def test_a_void_pointer_still_converts_to_itself(self):
        assert support.as_pointer(ctypes.c_void_p(WIDE)) == WIDE

    def test_a_null_handle_is_the_null_pointer(self):
        assert support.as_pointer(wgl_types().HDC()) == 0

    def test_an_egl_style_pointer_class_is_unaffected(self):
        """The pointer classes went through the branch that already worked."""
        from OpenGL._opaque import opaque_pointer_cls

        cls = opaque_pointer_cls('SomeHandle')
        assert support.as_pointer(ctypes.cast(ctypes.c_void_p(NARROW), cls)) == NARROW

    def test_an_integer_field_is_not_read_as_an_address(self):
        """The reason the test is `_type_ == 'P'` and not "has a .value"."""
        assert support.as_pointer(ctypes.c_int(1234)) != 1234


class TestAHandleComesBackAsWhatCtypesGives:
    """``opaque`` produces the object the ctypes restype would have.

    For a pointer class that is an instance of the class; for a pointer-sized
    simple type ctypes converts the result to a plain integer, and so must
    this.
    """

    @pytest.mark.parametrize('name', WGL_HANDLES)
    @pytest.mark.parametrize('address', [NARROW, WIDE])
    def test_a_wgl_handle_comes_back_as_an_integer(self, name, address):
        assert support.opaque(address, name) == address

    @pytest.mark.parametrize('name', WGL_HANDLES)
    def test_and_the_integer_is_what_the_restype_would_produce(self, name):
        """Measured against ctypes rather than asserted: the contract is that
        the two implementations cannot be told apart."""
        declared = getattr(wgl_types(), name)
        through_ctypes = declared(NARROW).__ctypes_from_outparam__()
        assert support.opaque(NARROW, name) == through_ctypes

    def test_a_handle_that_comes_back_can_be_passed_again(self):
        """The round trip is the point: what a call answers with is what the
        next call is given."""
        answered = support.opaque(WIDE, 'HDC')
        assert support.as_pointer(answered) == WIDE

    def test_a_pointer_class_still_comes_back_as_an_instance(self):
        """GL and EGL are unchanged: their handles are pointer classes, and a
        caller comparing two of them relies on getting the class back.

        ``GLsync`` rather than one of EGL's, so that this asks the question
        everywhere: EGL's declarations import only where there is an EGL
        library to declare against, and the answer is about the shape of the
        class, which is the same for both.
        """
        from OpenGL.raw.GL import _types

        result = support.opaque(NARROW, 'GLsync')
        assert isinstance(result, _types.GLsync)


class TestTheDeclarationsThisRestsOn:
    """If WGL ever declares its handles as pointer classes, the branch above
    stops being reachable and these say so."""

    @pytest.mark.parametrize('name', WGL_HANDLES)
    def test_a_wgl_handle_is_a_pointer_sized_simple_type(self, name):
        declared = getattr(wgl_types(), name)
        assert issubclass(declared, ctypes._SimpleCData)
        assert declared._type_ == 'P'

    @pytest.mark.parametrize('name', WGL_HANDLES)
    def test_and_it_is_not_a_pointer_class(self, name):
        assert not issubclass(getattr(wgl_types(), name), ctypes._Pointer)
