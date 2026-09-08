"""The Win32 calls behind :class:`OpenGL.Tk.win32.WGLContext` say what they are.

A handle is pointer-sized and ``ctypes`` gives an undeclared function a return
type of C ``int``, so an undeclared ``GetDC`` answers half an ``HDC``.  What
follows is a context that is refused on some windows and made on others,
reported as ``ERROR_INVALID_PIXEL_FORMAT`` -- see
:data:`OpenGL.Tk.win32.SIGNATURES`.

The module imports anywhere, so the table is held to Win32's own signatures
anywhere; what needs Windows is loading the libraries it is applied to.
"""

import ctypes
import inspect
import re
import sys

import pytest

from OpenGL.Tk import win32

needs_windows = pytest.mark.skipif(
    not sys.platform.startswith(('win32', 'cygwin')),
    reason='there is no Win32 library to declare anything on here')

#: How the module reaches an entry point: ``self._user32.GetDC(...)``.
CALL = re.compile(r'self\._(gdi32|user32)\.(\w+)')

#: What Win32 says these answer and take, in the terms of its own headers, so
#: the module's table is checked against the platform rather than against
#: itself.  A handle -- ``HWND``, ``HDC``, ``HMENU``, ``HINSTANCE`` -- and a
#: ``LPVOID`` are pointers; ``BOOL``, ``int`` and a pixel format index are C
#: ``int``; ``DWORD`` is 32 bits wide whatever the build.
DECLARED = {
    ('gdi32', 'ChoosePixelFormat'): ('int', ['pointer', 'pointer']),
    ('gdi32', 'SetPixelFormat'): ('int', ['pointer', 'int', 'pointer']),
    ('gdi32', 'SwapBuffers'): ('int', ['pointer']),
    ('user32', 'CreateWindowExW'): ('pointer', [
        'dword', 'wide string', 'wide string', 'dword',
        'int', 'int', 'int', 'int',
        'pointer', 'pointer', 'pointer', 'pointer',
    ]),
    ('user32', 'DestroyWindow'): ('int', ['pointer']),
    ('user32', 'GetDC'): ('pointer', ['pointer']),
    ('user32', 'ReleaseDC'): ('int', ['pointer', 'pointer']),
}


def kindOf(declared):
    """Which of :data:`DECLARED`'s kinds a ctypes type is

    By width and by what it carries rather than by name, since a name is not
    what a call gets wrong: an ``int`` standing in for a handle is the defect,
    whatever the alias in front of it is called.
    """
    if declared is ctypes.c_wchar_p:
        return 'wide string'
    if declared is ctypes.c_uint32:
        return 'dword'
    if hasattr(declared, 'contents') or getattr(declared, '_type_', None) == 'P':
        return 'pointer'
    if ctypes.sizeof(declared) == ctypes.sizeof(ctypes.c_int):
        return 'int'
    return 'something %d bytes wide' % (ctypes.sizeof(declared),)


def calls():
    """Every ``(library, entry point)`` the module calls through"""
    found = set(CALL.findall(inspect.getsource(win32)))
    assert found, 'no Win32 calls found; the pattern above has gone stale'
    return found


class TestTheTableSaysWhatWin32Says:
    def test_every_call_the_module_makes_is_in_it(self):
        """A call with no signature is one ctypes guesses the types of."""
        missing = calls() - set(win32.SIGNATURES)
        assert not missing, sorted(missing)

    def test_it_declares_nothing_the_module_does_not_call(self):
        stale = set(win32.SIGNATURES) - calls()
        assert not stale, sorted(stale)

    @pytest.mark.parametrize('entryPoint', sorted(DECLARED))
    def test_it_answers_what_win32_says_it_answers(self, entryPoint):
        restype = win32.SIGNATURES[entryPoint][0]
        assert kindOf(restype) == DECLARED[entryPoint][0], restype

    @pytest.mark.parametrize('entryPoint', sorted(DECLARED))
    def test_it_takes_what_win32_says_it_takes(self, entryPoint):
        argtypes = win32.SIGNATURES[entryPoint][1]
        assert [kindOf(each) for each in argtypes] == DECLARED[entryPoint][1]

    def test_a_device_context_is_the_whole_handle(self):
        """The one the defect turned on.

        A window whose ``HDC`` has its top bit set comes back negative through
        a C ``int``, and sign-extending that gives a different address from the
        one an undeclared call is handed -- so the pixel format is set on one
        device context and the context asked for on another.
        """
        restype, argtypes = win32.SIGNATURES[('user32', 'GetDC')]
        assert ctypes.sizeof(restype) == ctypes.sizeof(ctypes.c_void_p)
        assert ctypes.sizeof(argtypes[0]) == ctypes.sizeof(ctypes.c_void_p)


@needs_windows
class TestTheLibraryCarriesThem:
    def test_the_declarations_are_applied(self):
        for (name, entryPoint), (restype, argtypes) in sorted(
                win32.SIGNATURES.items()):
            declared = getattr(win32.windowsLibrary(name), entryPoint)
            assert declared.restype is restype, (name, entryPoint)
            assert list(declared.argtypes) == argtypes, (name, entryPoint)

    def test_the_same_library_comes_back(self):
        """A second ``WinDLL`` of the same name would carry no declarations."""
        assert win32.windowsLibrary('user32') is win32.windowsLibrary('user32')

    def test_nothing_is_declared_on_the_library_everyone_shares(self):
        """``ctypes.windll.user32`` is one object for the whole process.

        A prototype declared on it changes the signature under every other
        library calling through it, which is this defect handed to somebody
        else.
        """
        win32.windowsLibrary('user32')
        shared = ctypes.windll.user32.GetDC
        assert shared.restype is ctypes.c_int
        assert not shared.argtypes
