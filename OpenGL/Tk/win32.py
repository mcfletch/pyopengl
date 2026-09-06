"""An OpenGL context on a Tk widget's Windows window.

Tk gives out the ``HWND`` (``winfo_id()``); WGL makes a context against its
device context.  Two questions are asked of the driver, and
:func:`pixelFormatAttributes` and :func:`contextAttributes` are what a
:class:`~OpenGL.Tk.attributes.ContextAttributes` becomes for each.

**Both of the calls that answer them are extensions, and an extension entry
point can only be looked up while a context is already current.**  So a
throwaway context is made first, on a pixel format chosen by the ancient
``ChoosePixelFormat``, purely to have somewhere to ask from; the real format
and the real context are chosen through the extensions, and the throwaway is
destroyed.  This is the documented sequence and there is no shorter one.

**A window's pixel format is set once and cannot be changed**, which is why the
throwaway context is made on a window of its own rather than on the widget's:
setting a format on the widget to ask the question would spend the one chance
to set the format the answer names.
"""

from __future__ import annotations

import ctypes
import logging
from typing import Any, List

from OpenGL.Tk.attributes import ContextAttributes
from OpenGL.Tk.errors import TkContextError

log = logging.getLogger(__name__)

__all__ = ['WGLContext', 'contextAttributes', 'pixelFormatAttributes']


def _arb(name: str) -> Any:
    """One of PyOpenGL's WGL extension modules

    Imported on use rather than at module scope, because importing
    ``OpenGL.WGL`` loads ``opengl32``, which exists only on Windows -- and this
    module is imported wherever the package is, if only to be looked at.

    The constants and entry points in these modules arrive from the generated
    declaration tables as they are imported, so a checker reading the source
    finds none of them by name; ``Any`` is what there is to say about a table it
    cannot see.
    """
    import importlib

    return importlib.import_module('OpenGL.WGL.ARB.' + name)

#: What ``PIXELFORMATDESCRIPTOR.dwFlags`` needs for a window a GL context can
#: be made current on.  Named here rather than imported because the values are
#: part of the Win32 ABI and do not change.
PFD_DRAW_TO_WINDOW = 0x00000004
PFD_SUPPORT_OPENGL = 0x00000020
PFD_DOUBLEBUFFER = 0x00000001
PFD_TYPE_RGBA = 0
PFD_MAIN_PLANE = 0


def pixelFormatAttributes(attributes: ContextAttributes) -> List[int]:
    """The ``wglChoosePixelFormatARB`` attribute list a request asks for

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


def contextAttributes(attributes: ContextAttributes) -> List[int]:
    """The ``wglCreateContextAttribsARB`` attribute list a request asks for

    Terminated with 0.  A ``legacy`` request has nothing to say here and is
    created through ``wglCreateContext`` instead.
    """
    create_context = _arb('create_context')
    create_context_profile = _arb('create_context_profile')

    wanted: List[int] = []
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
    """What ``ChoosePixelFormat`` and ``SetPixelFormat`` describe a format with

    Only the fields this module sets are commented; the rest are laid out
    because the structure's size and order are its ABI.
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
    """The old-style format description a request amounts to

    What ``ChoosePixelFormat`` takes.  It is a request for the *nearest*
    format rather than a filter, so it always matches something; the
    extension-based choice is the one that honours multisampling and exact
    channel sizes.
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


class WGLContext(object):
    """A WGL context bound to the window a Tk widget owns

    Built by :func:`OpenGL.Tk.context.createContext`; a caller reaches it as
    ``frame.context``.

    Attributes:
        handle -- the ``HGLRC`` the driver made
        window -- the ``HWND`` Tk gave the widget
        deviceContext -- the ``HDC`` this draws through
    """

    handle = None
    deviceContext = None

    def __init__(self, widget: Any, attributes: ContextAttributes) -> None:
        from OpenGL import WGL

        self.attributes = attributes
        self._wgl = WGL
        # windll exists only on Windows, which is the only place this module
        # is ever constructed; see OpenGL.Tk.context, which picks by Tk's own
        # windowing system.
        windows: Any = ctypes
        self._gdi32 = windows.windll.gdi32
        self._user32 = windows.windll.user32
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
        """Settle this window's pixel format, which can only be done once"""
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

        None where the extension is not there to ask, which is what the
        old-style choice is the fallback for.  The dance around it is in
        :meth:`_withProbeContext`: an extension entry point cannot be looked up
        without a context, and this is the call that decides which context to
        make.
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

        The scratch window is why this is not simply done on the widget: a
        window's pixel format may be set once, so asking the question on the
        widget's own window would use up the one chance to answer it.  The
        answer -- a format index -- is valid for any window on the same device.
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
                yield True
            finally:
                self._wgl.wglMakeCurrent(None, None)
                if handle:
                    self._wgl.wglDeleteContext(handle)
                self._user32.ReleaseDC(window, device)
                self._user32.DestroyWindow(window)

        return probe()

    def _scratchWindow(self):
        """A hidden window to make the probe context on, or None

        ``STATIC`` is a class every Windows process already has registered, so
        there is no class to register and unregister for a window that exists
        for the length of two calls.
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
        """Make the context, saying why if the driver will not"""
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
            self._wgl.wglMakeCurrent(None, None)
            self._wgl.wglDeleteContext(old)
        return self._checked(handle)

    def _checked(self, handle):
        if not handle:
            raise TkContextError(
                'The driver would not create a context for %s'
                % (self.attributes.describe(),))
        return handle

    ### the context protocol
    def makeCurrent(self) -> bool:
        """Draw into this widget from now on; False if the driver refused"""
        if self.handle is None:
            return False
        return bool(self._wgl.wglMakeCurrent(self.deviceContext, self.handle))

    def releaseCurrent(self) -> None:
        """Let go of the current context, leaving none current"""
        self._wgl.wglMakeCurrent(None, None)

    def swapBuffers(self) -> None:
        """Show what has been drawn"""
        if self.handle is not None:
            self._gdi32.SwapBuffers(self.deviceContext)

    def setSwapInterval(self, interval: int) -> bool:
        """Wait ``interval`` refreshes between swaps; False if it cannot"""
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
        """Give the context and the device context back

        Called twice is called once; the second call has nothing to do.
        """
        if self.handle is not None:
            self.releaseCurrent()
            self._wgl.wglDeleteContext(self.handle)
            self.handle = None
        self._releaseDeviceContext()

    def _releaseDeviceContext(self) -> None:
        if self.deviceContext:
            self._user32.ReleaseDC(self.window, self.deviceContext)
            self.deviceContext = None

    def describe(self) -> str:
        """A one-line description of what this context is, for a log line"""
        return 'WGL context on window 0x%x for %s' % (
            self.window, self.attributes.describe())
