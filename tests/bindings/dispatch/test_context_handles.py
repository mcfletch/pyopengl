#! /usr/bin/env python3
"""The shapes a context handle arrives in.

:func:`OpenGL.dispatch.make_current` is documented for the handle
``OpenGL.platform.PLATFORM.GetCurrentContext()`` returns, and that is a
different kind of object on each platform.  WGL and CGL declare their getter
``c_void_p`` and so hand back a plain ``int``; GLX declares ``GLXContext``,
which is a pointer to an opaque struct, and hands back a ctypes pointer
object.  The dispatch tables are keyed by address, so each of those has to
arrive as the same integer.

``int()`` alone cannot do it.  Handed anything offering the buffer protocol --
which every ctypes object does -- it reads the bytes as a string of digits,
so a pointer is not rejected as the wrong kind of thing but rather accepted
and then found to be a misspelt number.
"""

import ctypes

import pytest

from OpenGL import dispatch

# Declared on every platform, so the shape WGL names a context by is covered
# from wherever the suite runs rather than only on Windows.
from OpenGL.raw.WGL._types import HGLRC


class ContextRec(ctypes.Structure):
    """Stands in for the opaque struct a platform names a context by."""

    _fields_ = [('opaque', ctypes.c_int)]


@pytest.fixture
def pointer_handle():
    """A handle in GLX's shape, with the address it should be read as.

    The record is reachable from the pointer, so it lives as long as the
    handle does and the address stays this one's.
    """
    record = ContextRec()
    return ctypes.pointer(record), ctypes.addressof(record)


class TestEveryPlatformsHandleIsReadAsAnAddress:
    def test_an_int_is_its_own_address(self):
        """What a ``c_void_p`` restype produces: WGL and CGL."""
        assert dispatch._as_address(0x4321) == 0x4321

    def test_a_pointer_is_read_as_what_it_points_at(self, pointer_handle):
        """What GLX produces."""
        handle, address = pointer_handle
        assert dispatch._as_address(handle) == address

    def test_a_void_pointer_is_read_as_its_value(self, pointer_handle):
        handle, address = pointer_handle
        assert dispatch._as_address(ctypes.c_void_p(address)) == address

    def test_a_wgl_handle_is_read_as_its_value(self):
        """What WGL produces.  ``HGLRC`` is pointer-sized but is not one of
        ctypes' pointer classes -- ctypes shares every reference to
        ``c_void_p``, and a shared one would disable the array machinery for
        everything else, so the handle types are declared as simple types
        whose ``_type_`` is ``'P'``.  Neither ``ctypes.cast`` nor an
        ``isinstance`` against a pointer class recognises one."""
        assert dispatch._as_address(HGLRC(0x1234)) == 0x1234

    @pytest.mark.parametrize('nothing', [
        None,
        ctypes.c_void_p(),
        ctypes.POINTER(ContextRec)(),
        HGLRC(),
    ], ids=['none', 'null-void-pointer', 'null-typed-pointer', 'null-wgl-handle'])
    def test_no_context_is_zero(self, nothing):
        """Which is the key the layer files a process's unnamed context under."""
        assert dispatch._as_address(nothing) == 0

    def test_a_one_element_array_holding_one_is_unwrapped(self, pointer_handle):
        """The shape a read-back pointer takes with ``SIZE_1_ARRAY_UNPACK`` off."""
        handle, address = pointer_handle
        holder = (ctypes.c_void_p * 1)(address)
        assert dispatch._as_address(holder) == address


class TestTheDispatchLayerTakesAHandleInAnyOfThoseShapes:
    """The layer keys its tables by address, so what a caller passes and what
    a caller passed last time have to compare equal however each arrived."""

    @pytest.fixture(autouse=True)
    def quiet(self, monkeypatch):
        """Leave the debug-output offer out of it, and put back what was
        current: these cases name contexts that do not exist."""
        was = dispatch._context_key()
        monkeypatch.setattr(dispatch, 'offer_debug_output', lambda: None)
        yield
        dispatch.make_current(was)

    def test_making_a_pointer_current_records_the_address(self, pointer_handle):
        handle, address = pointer_handle
        dispatch.make_current(handle)
        assert dispatch._context_key() == address

    def test_the_int_for_the_same_context_names_the_same_one(self,
                                                             pointer_handle):
        """A program that has the address and a toolkit that has the pointer
        are talking about one context."""
        handle, address = pointer_handle
        dispatch.make_current(handle)
        first = dispatch._context_key()
        dispatch.make_current(address)
        assert dispatch._context_key() == first

    def test_forgetting_a_pointer_forgets_that_address(self, pointer_handle,
                                                       monkeypatch):
        handle, address = pointer_handle
        monkeypatch.setattr(dispatch, '_installed_callbacks',
                            {address: object()})
        monkeypatch.setattr(dispatch, '_current_context', lambda: 0)
        dispatch.forget_context(handle)
        assert address not in dispatch._installed_callbacks


class TestTheDriversAnswerIsReadWhateverItsShape:
    """``_current_context`` asks the platform which context is current, and
    that answer decides whether a debug callback is handed back before its
    context goes.  Unread, it says the platform cannot be asked -- and the
    callback is left installed in a context that is about to stop existing."""

    def test_a_pointer_answer_names_that_context(self, pointer_handle,
                                                 monkeypatch):
        from OpenGL import platform

        handle, address = pointer_handle
        monkeypatch.setattr(platform.PLATFORM, 'GetCurrentContext',
                            lambda: handle, raising=False)
        assert dispatch._current_context() == address

    def test_a_platform_with_no_way_to_ask_says_so(self, monkeypatch):
        """None rather than 0, so the caller can tell 'no context' from
        'no answer'."""
        from OpenGL import platform

        def cannot():
            raise NotImplementedError('no way to ask on this platform')

        monkeypatch.setattr(platform.PLATFORM, 'GetCurrentContext', cannot,
                            raising=False)
        assert dispatch._current_context() is None
