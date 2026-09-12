#! /usr/bin/env python3
"""Asking WGL which extensions a context has.

WGL has no ``glGetString(GL_EXTENSIONS)``. The list comes from
``wglGetExtensionsStringARB``, which is itself an extension, so the querier has
to look the entry point up before it can ask -- and it gets back a C string
while every specifier reaching it from a generated module is Python text.

#7 is that mixture going wrong on Python 3: a ``str`` compared against the
``bytes`` the driver answered matched nothing, so ``from OpenGL.WGL.EXT import
swap_control`` found no extension and every call raised. Reported fixed in
2020 and disputed by a second reporter with nothing since, which is what these
cases settle: the text handling is held here, on any machine, and what is left
for a Windows machine to answer is only whether the driver lists the
extension.

https://github.com/mcfletch/pyopengl/issues/7
"""

import ctypes

import pytest

import OpenGL.platform
from OpenGL.raw.WGL import _types

#: What a driver answers ``wglGetExtensionsStringARB`` with: a single
#: space-separated C string, and no ``GL_`` names in it.
EXTENSION_STRING = (
    b'WGL_ARB_extensions_string WGL_EXT_swap_control '
    b'WGL_ARB_pixel_format WGL_ARB_create_context'
)


class EntryPoint:
    """A ctypes function object: callable, and with a settable ``restype``.

    A plain method will not do -- the querier declares the return type of
    ``wglGetCurrentDC`` before calling it, and a bound method has nowhere to
    put that.
    """

    def __init__(self, call):
        self._call = call
        self.restype = None
        self.argtypes = None

    def __call__(self, *args):
        return self._call(*args)


class FakeWGL:
    """A WGL that has a current device context and answers for extensions.

    Stands in for ``OpenGL.platform.PLATFORM``, which on Windows is where the
    querier reaches for ``wglGetCurrentDC``, the address of
    ``wglGetExtensionsStringARB``, and the calling convention to call it with.
    """

    def __init__(self, extension_string=EXTENSION_STRING, dc=1):
        self.extension_string = extension_string
        self.dc = dc
        #: Every name the querier asked for an address for.
        self.looked_up = []
        self.OpenGL = self
        self.WGL = self
        self.wglGetCurrentDC = EntryPoint(lambda: self.dc)

    def GetCurrentContext(self):
        """No context, so the querier caches on itself rather than in
        ``contextdata`` -- which wants a real context to hang a key on."""
        return None

    def getExtensionProcedure(self, name):
        self.looked_up.append(name)
        return 0xC0FFEE

    def functionTypeFor(self, dll):
        querier = self

        class FunctionType:
            def __init__(self, restype, *argtypes):
                self.restype = restype
                self.argtypes = argtypes

            def __call__(self, address):
                def call(dc):
                    assert dc == querier.dc, dc
                    return querier.extension_string

                return call

        return FunctionType


@pytest.fixture
def querier(monkeypatch):
    """A WGL querier of its own, with nothing cached on it.

    ``_WGLQuerier`` is a singleton in the module and caches the list it pulled;
    a fresh one keeps one case's answer out of the next. Registering itself
    with ``ExtensionQuerier`` is what ``__init__`` does, so it is taken off
    that list again afterwards -- ``hasExtension`` asks every registered
    querier, and a stray one built on a stand-in would answer for the rest of
    the run.
    """
    from OpenGL import extensions

    made = _types._WGLQuerier()
    try:
        yield made
    finally:
        if made in extensions.ExtensionQuerier.registered:
            extensions.ExtensionQuerier.registered.remove(made)


@pytest.fixture
def wgl(monkeypatch):
    """``PLATFORM`` is a WGL with the extensions above."""
    fake = FakeWGL()
    monkeypatch.setattr(OpenGL.platform, 'PLATFORM', fake)
    return fake


class TestPullingTheList:
    def test_it_is_the_names_the_driver_gave(self, querier, wgl):
        assert querier.pullExtensions() == EXTENSION_STRING.split()

    def test_the_names_are_bytes(self, querier, wgl):
        """Which is what every other querier answers, and what the comparison
        in ``ExtensionQuerier.__call__`` converts its specifier to."""
        for name in querier.pullExtensions():
            assert isinstance(name, bytes), repr(name)

    def test_the_entry_point_is_asked_for_by_a_bytes_name(self, querier, wgl):
        """``wglGetProcAddress`` takes a C string; handing it ``str`` is a
        ctypes.ArgumentError on the way out."""
        querier.pullExtensions()
        assert wgl.looked_up == [b'wglGetExtensionsStringARB']

    def test_the_device_context_is_declared_as_a_handle(self, querier, wgl):
        """An HDC is a handle, and ctypes' default ``c_int`` return drops the
        top half of one on a 64-bit build -- a valid-looking DC that belongs
        to nothing, which the driver then answers no extensions for."""
        querier.pullExtensions()
        assert wgl.wglGetCurrentDC.restype is _types.HDC


class TestAskingWhetherAnExtensionIsThere:
    """The specifier arrives as text; the list is bytes."""

    def test_a_text_specifier_matches(self, querier, wgl):
        assert querier('WGL_EXT_swap_control')

    def test_a_bytes_specifier_matches(self, querier, wgl):
        assert querier(b'WGL_EXT_swap_control')

    def test_an_extension_the_driver_does_not_list_is_not_claimed(
        self, querier, wgl
    ):
        assert not querier('WGL_NV_swap_group')

    def test_a_name_that_is_not_wgl_is_not_this_queriers_business(
        self, querier, wgl
    ):
        """It answers None rather than False, which is how ``hasExtension``
        tells "not mine" from "mine, and no"."""
        assert querier('GL_ARB_vertex_buffer_object') is None

    def test_the_list_is_pulled_once(self, querier, wgl):
        querier('WGL_EXT_swap_control')
        querier('WGL_ARB_pixel_format')
        assert len(wgl.looked_up) == 1


class TestAMachineThatCannotAnswer:
    def test_no_entry_point_is_no_answer_rather_than_an_error(
        self, querier, monkeypatch
    ):
        """``getExtensionProcedure`` answering None makes the function type
        constructor raise TypeError; the querier has no list to give and says
        so, rather than raising out of an ``import``."""

        class NoEntryPoint(FakeWGL):
            def getExtensionProcedure(self, name):
                raise TypeError('cannot construct a function from None')

        monkeypatch.setattr(OpenGL.platform, 'PLATFORM', NoEntryPoint())
        assert querier.pullExtensions() is None

    def test_a_platform_that_is_not_wgl_answers_an_empty_list(
        self, querier, monkeypatch
    ):
        """``PLATFORM.OpenGL`` with no ``wglGetCurrentDC`` on it: this querier
        is registered on every platform, and on the ones that are not Windows
        it simply has nothing to report."""

        class NotWindows:
            OpenGL = object()

            def GetCurrentContext(self):
                return None

        monkeypatch.setattr(OpenGL.platform, 'PLATFORM', NotWindows())
        assert querier.pullExtensions() == []
