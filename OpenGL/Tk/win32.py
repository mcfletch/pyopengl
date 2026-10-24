"""An OpenGL context on a Tk widget's Windows window.

Tk provides the ``HWND`` (``winfo_id()``), and WGL creates a context on its
device context in two steps: choose a pixel format, then create the context.
:func:`pixelFormatAttributes` and :func:`contextAttributes` translate a
:class:`~OpenGL.Tk.attributes.ContextAttributes` into the attribute list for
each step.

Both steps use extension functions (``wglChoosePixelFormatARB`` and
``wglCreateContextAttribsARB``).  An extension entry point can only be looked
up while a context is current.  A temporary context is therefore created
first, on a pixel format chosen by ``ChoosePixelFormat``.  The real format and
context are then chosen through the extensions, and the temporary context is
destroyed.  This is the sequence Microsoft documents.

A window's pixel format can be set only once.  The temporary context is
therefore created on a separate hidden window.  Setting a format on the
widget's window for the temporary context would prevent setting the format the
extension chooses.

Every Win32 entry point used here is declared in :data:`SIGNATURES` and loaded
through :func:`windowsLibrary` rather than ``ctypes.windll``.  See
:data:`SIGNATURES` for why handles need declared widths.
"""

from __future__ import annotations

import ctypes
import logging
from typing import Any

from OpenGL.error import end_abandoned_block
from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.context import gone, nowCurrent
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

__all__ = [
    'SIGNATURES', 'WGLContext', 'contextAttributes', 'pixelFormatAttributes',
    'windowsLibrary',
]


def _arb(name: str) -> Any:
    """One of PyOpenGL's WGL extension modules

    Imported on use rather than at module scope.  Importing ``OpenGL.WGL``
    loads ``opengl32``, which exists only on Windows, and this module can be
    imported on any platform.

    The constants and entry points in these modules come from the generated
    declaration tables at import time.  A type checker reading the source
    cannot find them by name, so the result is typed ``Any``.
    """
    import importlib

    return importlib.import_module('OpenGL.WGL.ARB.' + name)

#: The ``PIXELFORMATDESCRIPTOR`` values for a window a GL context can be made
#: current on.  Defined here because the values are part of the Win32 ABI and
#: do not change.
PFD_DRAW_TO_WINDOW = 0x00000004
PFD_SUPPORT_OPENGL = 0x00000020
PFD_DOUBLEBUFFER = 0x00000001
PFD_TYPE_RGBA = 0
PFD_MAIN_PLANE = 0


def pixelFormatAttributes(attributes: ContextAttributes) -> list[int]:
    """The ``wglChoosePixelFormatARB`` attribute list for ``attributes``

    Terminated with 0, as that call requires.
    """
    multisample, pixel_format = _arb('multisample'), _arb('pixel_format')

    wanted = [
        pixel_format.WGL_DRAW_TO_WINDOW_ARB, 1,
        pixel_format.WGL_SUPPORT_OPENGL_ARB, 1,
        pixel_format.WGL_ACCELERATION_ARB,
        pixel_format.WGL_FULL_ACCELERATION_ARB,
        pixel_format.WGL_PIXEL_TYPE_ARB, pixel_format.WGL_TYPE_RGBA_ARB,
        pixel_format.WGL_DOUBLE_BUFFER_ARB,
        1 if attributes.doubleBuffer else 0,
        pixel_format.WGL_RED_BITS_ARB, attributes.redSize,
        pixel_format.WGL_GREEN_BITS_ARB, attributes.greenSize,
        pixel_format.WGL_BLUE_BITS_ARB, attributes.blueSize,
        pixel_format.WGL_ALPHA_BITS_ARB, attributes.alphaSize,
        pixel_format.WGL_DEPTH_BITS_ARB, attributes.depthSize,
        pixel_format.WGL_STENCIL_BITS_ARB, attributes.stencilSize,
    ]
    if attributes.samples > 0:
        wanted += [multisample.WGL_SAMPLE_BUFFERS_ARB, 1,
                   multisample.WGL_SAMPLES_ARB, attributes.samples]
    if attributes.stereo:
        wanted += [pixel_format.WGL_STEREO_ARB, 1]
    return wanted + [0]


def contextAttributes(attributes: ContextAttributes) -> list[int]:
    """The ``wglCreateContextAttribsARB`` attribute list for ``attributes``

    Terminated with 0.  A ``legacy`` request is created through
    ``wglCreateContext`` instead.
    """
    create_context = _arb('create_context')
    create_context_profile = _arb('create_context_profile')

    wanted: list[int] = []
    if attributes.version:
        wanted += [
            create_context.WGL_CONTEXT_MAJOR_VERSION_ARB, attributes.version[0],
            create_context.WGL_CONTEXT_MINOR_VERSION_ARB, attributes.version[1],
        ]
    if attributes.profileApplies():
        wanted += [
            create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB,
            create_context_profile.WGL_CONTEXT_CORE_PROFILE_BIT_ARB
            if attributes.profile == 'core'
            else create_context_profile.WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB,
        ]
    flags = 0
    if attributes.forwardCompatibleApplies():
        flags |= create_context.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
    if attributes.debug:
        flags |= create_context.WGL_CONTEXT_DEBUG_BIT_ARB
    if flags:
        wanted += [create_context.WGL_CONTEXT_FLAGS_ARB, flags]
    return wanted + [0]


class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    """The pixel format description ``ChoosePixelFormat`` and
    ``SetPixelFormat`` take

    Every field is declared, including those this module never sets, because
    the structure's size and field order are part of the ABI.
    """

    _fields_ = [
        ('nSize', ctypes.c_ushort),
        ('nVersion', ctypes.c_ushort),
        ('dwFlags', ctypes.c_uint32),
        ('iPixelType', ctypes.c_ubyte),
        ('cColorBits', ctypes.c_ubyte),
        ('cRedBits', ctypes.c_ubyte),
        ('cRedShift', ctypes.c_ubyte),
        ('cGreenBits', ctypes.c_ubyte),
        ('cGreenShift', ctypes.c_ubyte),
        ('cBlueBits', ctypes.c_ubyte),
        ('cBlueShift', ctypes.c_ubyte),
        ('cAlphaBits', ctypes.c_ubyte),
        ('cAlphaShift', ctypes.c_ubyte),
        ('cAccumBits', ctypes.c_ubyte),
        ('cAccumRedBits', ctypes.c_ubyte),
        ('cAccumGreenBits', ctypes.c_ubyte),
        ('cAccumBlueBits', ctypes.c_ubyte),
        ('cAccumAlphaBits', ctypes.c_ubyte),
        ('cDepthBits', ctypes.c_ubyte),
        ('cStencilBits', ctypes.c_ubyte),
        ('cAuxBuffers', ctypes.c_ubyte),
        ('iLayerType', ctypes.c_ubyte),
        ('bReserved', ctypes.c_ubyte),
        ('dwLayerMask', ctypes.c_uint32),
        ('dwVisibleMask', ctypes.c_uint32),
        ('dwDamageMask', ctypes.c_uint32),
    ]


def describedFormat(attributes: ContextAttributes) -> PIXELFORMATDESCRIPTOR:
    """The ``PIXELFORMATDESCRIPTOR`` for ``attributes``

    ``ChoosePixelFormat`` takes this and returns the nearest format, so it
    always finds one.  Only ``wglChoosePixelFormatARB`` honours multisampling
    and exact channel sizes.
    """
    described = PIXELFORMATDESCRIPTOR()
    described.nSize = ctypes.sizeof(PIXELFORMATDESCRIPTOR)
    described.nVersion = 1
    described.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL
    if attributes.doubleBuffer:
        described.dwFlags |= PFD_DOUBLEBUFFER
    described.iPixelType = PFD_TYPE_RGBA
    described.cColorBits = (attributes.redSize + attributes.greenSize
                            + attributes.blueSize)
    described.cAlphaBits = attributes.alphaSize
    described.cDepthBits = attributes.depthSize
    described.cStencilBits = attributes.stencilSize
    described.iLayerType = PFD_MAIN_PLANE
    return described


#: Win32 type names, so the signatures below match the platform headers.  Every
#: handle is pointer-sized, and ``BOOL`` is a C ``int``.
HWND = HDC = HMENU = HINSTANCE = LPVOID = ctypes.c_void_p
BOOL = ctypes.c_int
DWORD = ctypes.c_uint32
LPCWSTR = ctypes.c_wchar_p
PPIXELFORMATDESCRIPTOR = ctypes.POINTER(PIXELFORMATDESCRIPTOR)

#: Every Win32 entry point this module calls, keyed by ``(library, name)``,
#: with its return type and argument types.
#:
#: A 64-bit build requires these declarations.  ``ctypes`` gives an undeclared
#: function a C ``int`` return type, which is half the width of a handle.  An
#: undeclared ``GetDC`` returns the low 32 bits of the ``HDC`` as a signed
#: number.  ``SetPixelFormat``, with undeclared arguments, then receives that
#: value zero-extended.  ``wglCreateContext``, whose ``HDC`` is declared,
#: receives it sign-extended.  The format is set on one device context and the
#: context is requested on another.  The driver returns no context and
#: ``ERROR_INVALID_PIXEL_FORMAT``, which does not mention the handle.
#:
#: Whether this fails depends on the handle's value, so the same program can
#: create a context on one window and fail on the next.
SIGNATURES: dict[tuple[str, str], tuple[Any, list[Any]]] = {
    ('gdi32', 'ChoosePixelFormat'): (
        ctypes.c_int, [HDC, PPIXELFORMATDESCRIPTOR]),
    ('gdi32', 'SetPixelFormat'): (
        BOOL, [HDC, ctypes.c_int, PPIXELFORMATDESCRIPTOR]),
    ('gdi32', 'SwapBuffers'): (BOOL, [HDC]),
    ('user32', 'CreateWindowExW'): (HWND, [
        DWORD, LPCWSTR, LPCWSTR, DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        HWND, HMENU, HINSTANCE, LPVOID,
    ]),
    ('user32', 'DestroyWindow'): (BOOL, [HWND]),
    ('user32', 'GetDC'): (HDC, [HWND]),
    ('user32', 'ReleaseDC'): (ctypes.c_int, [HWND, HDC]),
}

#: The libraries :func:`windowsLibrary` has loaded, by name.
_LIBRARIES: dict[str, Any] = {}


def windowsLibrary(name: str) -> Any:
    """``name``.dll, with the entry points :data:`SIGNATURES` names declared

    This module loads its own library object.  ``ctypes.windll.<name>`` is
    shared by all code in the process, and a prototype declared on it changes
    the signature for every other caller.
    """
    library = _LIBRARIES.get(name)
    if library is None:
        # windll and WinDLL exist only on Windows, which is the only place
        # this is called.  OpenGL.Tk.context picks the implementation from
        # Tk's windowing system.
        windows: Any = ctypes
        library = _LIBRARIES[name] = windows.WinDLL(name)
        for (where, entryPoint), (restype, argtypes) in SIGNATURES.items():
            if where == name:
                declared = getattr(library, entryPoint)
                declared.restype = restype
                declared.argtypes = argtypes
    return library


class WGLContext(object):
    """A WGL context bound to the window a Tk widget owns

    Created by :func:`OpenGL.Tk.context.createContext` and available as
    ``frame.context``.

    Attributes:
        handle - the driver's ``HGLRC``
        window - the widget's ``HWND``
        deviceContext - the ``HDC`` this context draws through
    """

    handle = None
    deviceContext = None

    def __init__(self, widget: Any, attributes: ContextAttributes) -> None:
        from OpenGL import WGL

        self.attributes = attributes
        self._wgl = WGL
        self._gdi32 = windowsLibrary('gdi32')
        self._user32 = windowsLibrary('user32')
        self.window = int(widget.winfo_id())
        self.deviceContext = self._user32.GetDC(self.window)
        if not self.deviceContext:
            raise TkContextError(
                'Could not get a device context for the Tk window 0x%x'
                % (self.window,))
        try:
            self._chooseAndSetFormat()
            self.handle = self._create()
        except Exception:
            self._releaseDeviceContext()
            raise

    ### creation
    def _chooseAndSetFormat(self) -> None:
        """Choose and set this window's pixel format, which is set only once"""
        described = describedFormat(self.attributes)
        index = self._extensionFormat()
        if index is None:
            index = self._gdi32.ChoosePixelFormat(self.deviceContext,
                                                  ctypes.byref(described))
        if not index:
            raise TkContextError(
                'No pixel format matches %s' % (self.attributes.describe(),))
        if not self._gdi32.SetPixelFormat(self.deviceContext, index,
                                          ctypes.byref(described)):
            raise TkContextError(
                'Windows would not set pixel format %d on this window; a '
                'window\'s format can only be set once' % (index,))

    def _extensionFormat(self):
        """The format ``wglChoosePixelFormatARB`` picks, or None

        Returns None when the extension is missing, and the caller falls back
        to ``ChoosePixelFormat``.  An extension entry point cannot be looked up
        without a current context, so the call runs inside
        :meth:`_withProbeContext`.
        """
        pixel_format = _arb('pixel_format')

        wanted = pixelFormatAttributes(self.attributes)
        with self._withProbeContext() as available:
            if not available or not pixel_format.wglChoosePixelFormatARB:
                return None
            formats = (ctypes.c_int * 1)()
            count = ctypes.c_uint(0)
            ok = pixel_format.wglChoosePixelFormatARB(
                self.deviceContext,
                (ctypes.c_int * len(wanted))(*wanted),
                None, 1, formats, ctypes.byref(count),
            )
            if ok and count.value:
                return int(formats[0])
        return None

    def _withProbeContext(self):
        """A context on a scratch window, current for the body

        A window's pixel format can be set only once.  Setting one on the
        widget's window for this probe would prevent setting the chosen
        format later.  The chosen format index is valid for any window on the
        same device.
        """
        import contextlib

        @contextlib.contextmanager
        def probe():
            window = self._scratchWindow()
            if window is None:
                yield False
                return
            device = self._user32.GetDC(window)
            handle = None
            try:
                described = describedFormat(self.attributes)
                index = self._gdi32.ChoosePixelFormat(device,
                                                      ctypes.byref(described))
                if not index or not self._gdi32.SetPixelFormat(
                        device, index, ctypes.byref(described)):
                    yield False
                    return
                handle = self._wgl.wglCreateContext(device)
                if not handle:
                    yield False
                    return
                self._wgl.wglMakeCurrent(device, handle)
                nowCurrent(handle)
                yield True
            finally:
                if handle:
                    gone(handle)
                self._wgl.wglMakeCurrent(None, None)
                if handle:
                    self._wgl.wglDeleteContext(handle)
                nowCurrent(None)
                self._user32.ReleaseDC(window, device)
                self._user32.DestroyWindow(window)

        return probe()

    def _scratchWindow(self):
        """A hidden window for the probe context, or None

        ``STATIC`` is a window class registered in every Windows process, so
        no class needs to be registered for this short-lived window.
        """
        WS_OVERLAPPED = 0x00000000
        window = self._user32.CreateWindowExW(
            0, 'STATIC', 'PyOpenGL probe', WS_OVERLAPPED,
            0, 0, 1, 1, None, None, None, None,
        )
        if not window:
            log.debug('could not make a scratch window to probe WGL with')
            return None
        return window

    def _create(self):
        """The new context handle; raises TkContextError with the reason"""
        create_context = _arb('create_context')

        share = getattr(self.attributes.share, 'handle',
                        self.attributes.share) or None
        if self.attributes.version is None and self.attributes.profile == 'legacy':
            return self._checked(self._wgl.wglCreateContext(self.deviceContext))
        old = self._wgl.wglCreateContext(self.deviceContext)
        if not old:
            raise TkContextError(
                'Windows would not create any GL context on this window')
        try:
            self._wgl.wglMakeCurrent(self.deviceContext, old)
            nowCurrent(old)
            if not create_context.wglCreateContextAttribsARB:
                raise TkContextError(
                    'This driver has no WGL_ARB_create_context, so it cannot '
                    'be asked for %s; ask for profile="legacy" to take '
                    'whatever it offers' % (self.attributes.describe(),))
            wanted = contextAttributes(self.attributes)
            handle = create_context.wglCreateContextAttribsARB(
                self.deviceContext, share,
                (ctypes.c_int * len(wanted))(*wanted),
            )
        finally:
            gone(old)
            self._wgl.wglMakeCurrent(None, None)
            self._wgl.wglDeleteContext(old)
            nowCurrent(None)
        return self._checked(handle)

    def _checked(self, handle):
        if not handle:
            raise TkContextError(
                'The driver would not create a context for %s'
                % (self.attributes.describe(),))
        return handle

    ### the context protocol
    def makeCurrent(self) -> bool:
        """Make this context current; False if the driver refused"""
        if self.handle is None:
            return False
        made = bool(self._wgl.wglMakeCurrent(self.deviceContext, self.handle))
        if made:
            nowCurrent(self.handle)
        return made

    def releaseCurrent(self) -> None:
        """Release the current context, leaving none current"""
        self._wgl.wglMakeCurrent(None, None)
        nowCurrent(None)

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self.handle is not None:
            self._gdi32.SwapBuffers(self.deviceContext)

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if unsupported"""
        import importlib

        swap_control: Any = importlib.import_module(
            'OpenGL.WGL.EXT.swap_control')
        if not swap_control.wglSwapIntervalEXT:
            return False
        try:
            return bool(swap_control.wglSwapIntervalEXT(int(interval)))
        except Exception:
            log.debug('the driver would not set the swap interval',
                      exc_info=True)
            return False

    def destroy(self) -> None:
        """Delete the context and release the device context

        A second call does nothing.

        An open ``glBegin`` block is closed first.  Destroying a context inside
        one is undefined behaviour, and some drivers crash.  See
        :func:`OpenGL.error.end_abandoned_block`.
        """
        if self.handle is not None:
            end_abandoned_block()
            gone(self.handle)
            self.releaseCurrent()
            self._wgl.wglDeleteContext(self.handle)
            self.handle = None
        self._releaseDeviceContext()

    def _releaseDeviceContext(self) -> None:
        if self.deviceContext:
            self._user32.ReleaseDC(self.window, self.deviceContext)
            self.deviceContext = None

    def describe(self) -> str:
        """A one-line description of this context, for a log line"""
        return 'WGL context on window 0x%x for %s' % (
            self.window, self.attributes.describe())
