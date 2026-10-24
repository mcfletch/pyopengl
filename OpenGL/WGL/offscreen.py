"""Offscreen OpenGL contexts on Windows, rendering to a pbuffer.

WGL (the Windows OpenGL interface) binds a rendering context to a *device
context*, which Windows creates for a window, a bitmap or a printer.  WGL has
no call to create a context on an adapter, as EGL has, and no windowless
context, as CGL has.  It has the pbuffer, a drawable the driver allocates in
its own memory.  A pbuffer has its own device context, which belongs to no
window and is never displayed.  This module renders to a pbuffer::

    from OpenGL.WGL.offscreen import headless_context

    with headless_context(width=640, height=480) as context:
        ...                                 # the context is current here

The pbuffer is the context's default framebuffer.  ``glClear``,
``glReadPixels`` and screenshots work as they do on a window.  (A CGL
offscreen context has no default framebuffer, and must bind a framebuffer
object before drawing.)

The module creates one hidden window per process.  The functions that create
the pbuffer and context (``wglChoosePixelFormatARB``, ``wglCreatePbufferARB``
and ``wglCreateContextAttribsARB``) are WGL extensions.  Extension entry
points are resolved with ``wglGetProcAddress``, which works only while a
context is current.  :func:`bootstrap` therefore creates a window, sets a pixel
format on its device context, and creates an OpenGL 1.1 context on it, used
only to resolve those entry points.  The window is 1x1 and ``WS_POPUP``.  It
is never shown and has no message loop.  The pbuffer is not tied to the
window, and can outlive it.

The window needs a window station and a desktop, which a service running in
session 0 has.  It does not need a visible display, a compositor, a logged-in
session or an open remote-desktop connection.

The driver must offer ``WGL_ARB_pbuffer``, ``WGL_ARB_pixel_format`` and
``WGL_ARB_create_context``.  Every hardware OpenGL driver for Windows has
offered them since about 2009.  Microsoft's GDI generic implementation, used
on a machine with no vendor driver installed, offers none of them and supports
only OpenGL 1.1.  :func:`available` returns the extensions this machine is
missing.  Construction raises :class:`WGLError` naming the missing extensions,
so an application can try an offscreen context and fall back to something
else.

The Mesa and ANGLE builds for Windows provide EGL, which ``OpenGL.EGL``
supports.  ANGLE provides OpenGL ES and no desktop GL.
"""

import contextlib
import ctypes
import sys

__all__ = (
    'ACCELERATION_KINDS',
    'PROFILES',
    'REQUIRED_EXTENSIONS',
    'OffscreenContext',
    'WGLError',
    'available',
    'bootstrap',
    'context_attributes',
    'headless_context',
    'pixel_format_attributes',
    'release_bootstrap',
    'wgl_extensions',
)


class WGLError(RuntimeError):
    """A WGL or Win32 call failed, or the machine cannot meet the request.

    ``operation`` names the call.  ``code`` is the ``GetLastError`` value, or
    zero if there was none.  A caller can use these to tell a driver without
    pbuffers from a size that is too large, without parsing the message.
    """

    def __init__(self, operation, code=0):
        self.operation = operation
        self.code = code
        if code:
            super().__init__('%s (Windows error %d)' % (operation, code))
        else:
            super().__init__(operation)


# -- Win32 declarations -----------------------------------------------------
#
# The eight Win32 functions this module uses are declared here, so PyOpenGL
# needs no wrapper package beyond ctypes.
#
# They use plain ctypes types instead of ``ctypes.wintypes``, and are loaded on
# first use.  The module therefore imports on any platform, and the functions
# that build attribute lists can be tested there.  A handle is ``c_void_p``.
# Windows documents USER and GDI handles as 32-bit values sign-extended to 64
# bits, so a narrower type would lose the top half of many real handles.

_HANDLE = ctypes.c_void_p
_DWORD = ctypes.c_uint32
_WORD = ctypes.c_uint16


class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    """The pixel format description ``ChoosePixelFormat`` and
    ``SetPixelFormat`` take.

    Only the bootstrap window uses it.  The pbuffer's format comes from
    :func:`pixel_format_attributes` and ``wglChoosePixelFormatARB``, the only
    call that can require a format able to draw to a pbuffer.
    """

    _fields_ = [
        ('nSize', _WORD), ('nVersion', _WORD),
        ('dwFlags', _DWORD), ('iPixelType', ctypes.c_ubyte),
        ('cColorBits', ctypes.c_ubyte), ('cRedBits', ctypes.c_ubyte),
        ('cRedShift', ctypes.c_ubyte), ('cGreenBits', ctypes.c_ubyte),
        ('cGreenShift', ctypes.c_ubyte), ('cBlueBits', ctypes.c_ubyte),
        ('cBlueShift', ctypes.c_ubyte), ('cAlphaBits', ctypes.c_ubyte),
        ('cAlphaShift', ctypes.c_ubyte), ('cAccumBits', ctypes.c_ubyte),
        ('cAccumRedBits', ctypes.c_ubyte), ('cAccumGreenBits', ctypes.c_ubyte),
        ('cAccumBlueBits', ctypes.c_ubyte), ('cAccumAlphaBits', ctypes.c_ubyte),
        ('cDepthBits', ctypes.c_ubyte), ('cStencilBits', ctypes.c_ubyte),
        ('cAuxBuffers', ctypes.c_ubyte), ('iLayerType', ctypes.c_ubyte),
        ('bReserved', ctypes.c_ubyte), ('dwLayerMask', _DWORD),
        ('dwVisibleMask', _DWORD), ('dwDamageMask', _DWORD),
    ]


class WNDCLASSW(ctypes.Structure):
    """The window class the bootstrap window is registered under.

    ``lpfnWndProc`` is a plain pointer set to the address of
    ``DefWindowProcW``.  The window handles no messages itself, so there is no
    Python callback to declare or keep alive.
    """

    _fields_ = [
        ('style', ctypes.c_uint),
        ('lpfnWndProc', ctypes.c_void_p),
        ('cbClsExtra', ctypes.c_int),
        ('cbWndExtra', ctypes.c_int),
        ('hInstance', _HANDLE),
        ('hIcon', _HANDLE),
        ('hCursor', _HANDLE),
        ('hbrBackground', _HANDLE),
        ('lpszMenuName', ctypes.c_wchar_p),
        ('lpszClassName', ctypes.c_wchar_p),
    ]


_LPPFD = ctypes.POINTER(PIXELFORMATDESCRIPTOR)


class _Win32:
    """The USER32/GDI32/KERNEL32 calls the bootstrap window is built from."""

    def __init__(self):
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        declare = (
            (self.user32.RegisterClassW, [ctypes.POINTER(WNDCLASSW)], _WORD),
            (self.user32.CreateWindowExW,
             [_DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p, _DWORD,
              ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
              _HANDLE, _HANDLE, _HANDLE, ctypes.c_void_p], _HANDLE),
            (self.user32.DestroyWindow, [_HANDLE], ctypes.c_int),
            (self.user32.GetDC, [_HANDLE], _HANDLE),
            (self.user32.ReleaseDC, [_HANDLE, _HANDLE], ctypes.c_int),
            (self.kernel32.GetModuleHandleW, [ctypes.c_wchar_p], _HANDLE),
            (self.gdi32.ChoosePixelFormat, [_HANDLE, _LPPFD], ctypes.c_int),
            (self.gdi32.SetPixelFormat,
             [_HANDLE, ctypes.c_int, _LPPFD], ctypes.c_int),
        )
        for function, argtypes, restype in declare:
            function.argtypes = argtypes
            function.restype = restype
        self.user32.DefWindowProcW.restype = ctypes.c_longlong


_win32 = None


def win32():
    """The Win32 entry points, loaded and declared on first use.

    Raises :class:`WGLError` on a platform without ``ctypes.WinDLL``.  The
    message names the modules to use on Linux and macOS.
    """
    global _win32
    if _win32 is None:
        if not hasattr(ctypes, 'WinDLL'):
            raise WGLError(
                'WGL is the Windows binding for OpenGL and this is %s; use '
                'OpenGL.EGL for offscreen rendering on Linux, or OpenGL.CGL '
                'on macOS' % (sys.platform,))
        _win32 = _Win32()
    return _win32

#: ``CS_OWNDC``: the window keeps its own device context instead of borrowing
#: one from a shared pool.  The pixel format is set on the device context, and
#: a borrowed device context loses it when returned to the pool.
_CS_OWNDC = 0x0020

#: ``WS_POPUP``: no frame, no caption and no parent.  Without ``WS_VISIBLE``
#: the window is not shown.
_WS_POPUP = 0x80000000

_PFD_DRAW_TO_WINDOW = 0x00000004
_PFD_SUPPORT_OPENGL = 0x00000020
_PFD_TYPE_RGBA = 0

#: ``ERROR_CLASS_ALREADY_EXISTS`` from ``RegisterClass``.  It means the class
#: is already registered, and is not treated as a failure.
_ERROR_CLASS_ALREADY_EXISTS = 1410

#: The class the bootstrap window is registered under.  Registration is per
#: module instance, so the name must not clash with another class.
_WINDOW_CLASS = 'PyOpenGLOffscreenBootstrap'


# -- request options ----------------------------------------------------------

#: The context profiles ``wglCreateContextAttribsARB`` offers, keyed by the
#: names this module uses.  ``'legacy'`` requests no profile, so the driver
#: uses its default.  It is the only choice below GL 3.2.
PROFILES = ('core', 'compatibility', 'legacy')

#: Whether the pixel format must be GPU-accelerated.  ``'accelerated'``
#: requires full acceleration.  ``'any'`` accepts any format the driver has,
#: which a machine with an unusual or virtualised adapter may need.
ACCELERATION_KINDS = ('accelerated', 'any')

#: The extensions an offscreen context needs.  :func:`available` returns the
#: names of any the driver lacks.
REQUIRED_EXTENSIONS = (
    'WGL_ARB_pixel_format',
    'WGL_ARB_pbuffer',
    'WGL_ARB_create_context',
)

#: Also required for a named profile.  Without it the only context available
#: is the driver's default, ``'legacy'``.
PROFILE_EXTENSION = 'WGL_ARB_create_context_profile'


def pixel_format_attributes(
    color_bits=24,
    alpha_bits=8,
    depth_bits=24,
    stencil_bits=8,
    samples=0,
    double_buffer=False,
    acceleration='accelerated',
):
    """The attribute list ``wglChoosePixelFormatARB`` takes, as plain integers.

    The function makes no WGL calls, so it runs on any platform.  The sizes
    are bits per buffer.  As in WGL, ``color_bits`` counts the three colour
    channels together.  A size of zero or less is left out of the list, so the
    driver picks it.

    ``WGL_DRAW_TO_PBUFFER_ARB`` is always requested.  ``ChoosePixelFormat``
    cannot express it, and the driver refuses to create a pbuffer with a
    format that lacks it.

    The list ends with a zero, as WGL requires.
    """
    from OpenGL.WGL.ARB import multisample, pbuffer, pixel_format

    if acceleration not in ACCELERATION_KINDS:
        raise ValueError('acceleration must be one of %r, not %r'
                         % (list(ACCELERATION_KINDS), acceleration))
    attributes = [
        pbuffer.WGL_DRAW_TO_PBUFFER_ARB, 1,
        pixel_format.WGL_SUPPORT_OPENGL_ARB, 1,
        pixel_format.WGL_PIXEL_TYPE_ARB, pixel_format.WGL_TYPE_RGBA_ARB,
        pixel_format.WGL_COLOR_BITS_ARB, int(color_bits),
        # Always stated, because a format matches if it has at least what was
        # requested.  An offscreen surface is never presented, so a back
        # buffer would waste memory.
        pixel_format.WGL_DOUBLE_BUFFER_ARB, 1 if double_buffer else 0,
    ]
    if acceleration == 'accelerated':
        attributes += [pixel_format.WGL_ACCELERATION_ARB,
                       pixel_format.WGL_FULL_ACCELERATION_ARB]
    if alpha_bits > 0:
        attributes += [pixel_format.WGL_ALPHA_BITS_ARB, int(alpha_bits)]
    if depth_bits > 0:
        attributes += [pixel_format.WGL_DEPTH_BITS_ARB, int(depth_bits)]
    if stencil_bits > 0:
        attributes += [pixel_format.WGL_STENCIL_BITS_ARB, int(stencil_bits)]
    if samples > 0:
        attributes += [multisample.WGL_SAMPLE_BUFFERS_ARB, 1,
                       multisample.WGL_SAMPLES_ARB, int(samples)]
    attributes.append(0)
    return attributes


def context_attributes(profile='core', version=(3, 3), debug=False,
                       forward_compatible=False):
    """The attribute list ``wglCreateContextAttribsARB`` takes.

    Like :func:`pixel_format_attributes`, it makes no WGL calls.  ``profile``
    is one of :data:`PROFILES`.  ``'legacy'`` sets no profile bit, as a
    request below GL 3.2 must.  The profile mask does not exist below 3.2, and
    a driver given one refuses the request.
    """
    from OpenGL.WGL.ARB import create_context, create_context_profile

    if profile not in PROFILES:
        raise ValueError('profile must be one of %r, not %r'
                         % (list(PROFILES), profile))
    major, minor = version
    attributes = [
        create_context.WGL_CONTEXT_MAJOR_VERSION_ARB, int(major),
        create_context.WGL_CONTEXT_MINOR_VERSION_ARB, int(minor),
    ]
    if profile != 'legacy':
        attributes += [
            create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB,
            create_context_profile.WGL_CONTEXT_CORE_PROFILE_BIT_ARB
            if profile == 'core'
            else create_context_profile.WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB,
        ]
    flags = 0
    if debug:
        flags |= create_context.WGL_CONTEXT_DEBUG_BIT_ARB
    if forward_compatible:
        flags |= create_context.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB
    if flags:
        attributes += [create_context.WGL_CONTEXT_FLAGS_ARB, flags]
    attributes.append(0)
    return attributes


def _ints(values):
    return (ctypes.c_int * len(values))(*[int(value) for value in values])


# -- the bootstrap ----------------------------------------------------------

class _Bootstrap:
    """A hidden window and an OpenGL 1.1 context on it, to resolve WGL from.

    :func:`bootstrap` creates one per process.  The calls that create an
    offscreen context are extensions, and an extension entry point resolves
    only while a context is current.  Nothing is drawn with this context.
    """

    hwnd = None
    dc = None
    context = None

    def __init__(self):
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC

        api = win32()
        self._register_class()
        self.hwnd = api.user32.CreateWindowExW(
            0, _WINDOW_CLASS, _WINDOW_CLASS, _WS_POPUP, 0, 0, 1, 1,
            None, None, self._instance, None,
        )
        if not self.hwnd:
            raise WGLError('CreateWindowEx for the bootstrap window',
                           ctypes.get_last_error())
        try:
            self.dc = api.user32.GetDC(self.hwnd)
            if not self.dc:
                raise WGLError('GetDC for the bootstrap window',
                               ctypes.get_last_error())
            self._set_pixel_format()
            self.context = WGL.wglCreateContext(HDC(self.dc))
            if not self.context:
                raise WGLError('wglCreateContext for the bootstrap context',
                               ctypes.get_last_error())
        except BaseException:
            self.release()
            raise

    _instance = None

    @classmethod
    def _register_class(cls):
        """Register the window class, once per process."""
        if cls._instance is not None:
            return
        api = win32()
        instance = api.kernel32.GetModuleHandleW(None)
        declaration = WNDCLASSW()
        declaration.style = _CS_OWNDC
        declaration.lpfnWndProc = ctypes.cast(
            api.user32.DefWindowProcW, ctypes.c_void_p)
        declaration.hInstance = instance
        declaration.lpszClassName = _WINDOW_CLASS
        if not api.user32.RegisterClassW(ctypes.byref(declaration)):
            code = ctypes.get_last_error()
            # ERROR_CLASS_ALREADY_EXISTS happens with a second interpreter in
            # the same process, or a reloaded module.
            if code != _ERROR_CLASS_ALREADY_EXISTS:
                raise WGLError('RegisterClass for the bootstrap window', code)
        # Kept for the life of the process.  Windows reads the class from this
        # structure for as long as it is registered.
        cls._declaration = declaration
        cls._instance = instance

    def _set_pixel_format(self):
        """Set a pixel format that supports OpenGL; nothing is drawn on it."""
        api = win32()
        descriptor = PIXELFORMATDESCRIPTOR()
        descriptor.nSize = ctypes.sizeof(descriptor)
        descriptor.nVersion = 1
        descriptor.dwFlags = _PFD_DRAW_TO_WINDOW | _PFD_SUPPORT_OPENGL
        descriptor.iPixelType = _PFD_TYPE_RGBA
        descriptor.cColorBits = 32
        descriptor.cDepthBits = 24
        descriptor.cStencilBits = 8
        chosen = api.gdi32.ChoosePixelFormat(self.dc, ctypes.byref(descriptor))
        if not chosen:
            raise WGLError('ChoosePixelFormat for the bootstrap window',
                           ctypes.get_last_error())
        if not api.gdi32.SetPixelFormat(
            self.dc, chosen, ctypes.byref(descriptor)
        ):
            raise WGLError('SetPixelFormat for the bootstrap window',
                           ctypes.get_last_error())

    @contextlib.contextmanager
    def current(self):
        """Make the bootstrap context current for the body, then restore the
        previous context.

        An application that had its own context current when it created an
        offscreen context gets that context back.
        """
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC, HGLRC

        was_dc = WGL.wglGetCurrentDC()
        was_context = WGL.wglGetCurrentContext()
        if not WGL.wglMakeCurrent(HDC(self.dc), HGLRC(self.context)):
            raise WGLError('wglMakeCurrent for the bootstrap context',
                           ctypes.get_last_error())
        try:
            yield self
        finally:
            WGL.wglMakeCurrent(HDC(was_dc or 0), HGLRC(was_context or 0))

    def release(self):
        """Destroy the GL context, release the device context and destroy the
        window."""
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HGLRC

        api = win32()
        if self.context:
            WGL.wglDeleteContext(HGLRC(self.context))
            self.context = None
        if self.dc:
            api.user32.ReleaseDC(self.hwnd, self.dc)
            self.dc = None
        if self.hwnd:
            api.user32.DestroyWindow(self.hwnd)
            self.hwnd = None


_bootstrap = None


def bootstrap():
    """The process's hidden bootstrap window, built on first use.

    One window serves every offscreen context in the process.  The device
    context passed to ``wglCreatePbufferARB`` selects the device, and the pixel
    format passed with it selects the buffers.
    """
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = _Bootstrap()
    return _bootstrap


def release_bootstrap():
    """Destroy the bootstrap window and context, if they exist.

    Calling this is optional.  The hidden 1x1 window and its OpenGL 1.1
    context use very little, and are freed when the process ends.  A test of
    the bootstrap rebuild, or an application unloading a plug-in, can call it.
    Existing offscreen contexts keep working, because a pbuffer is not tied to
    the window it was created through.
    """
    global _bootstrap
    if _bootstrap is not None:
        _bootstrap.release()
        _bootstrap = None


def wgl_extensions():
    """The WGL extension names this machine offers, as a frozenset.

    Empty if the extension string cannot be read.  The GDI generic
    implementation exports no ``wglGetExtensionsStringARB``, so it returns an
    empty set.
    """
    from OpenGL.raw.WGL._types import HDC
    from OpenGL.WGL.ARB import extensions_string

    with bootstrap().current() as booted:
        if not extensions_string.wglGetExtensionsStringARB:
            return frozenset()
        reported = extensions_string.wglGetExtensionsStringARB(HDC(booted.dc))
    if not reported:
        return frozenset()
    return frozenset(reported.decode('ascii', 'replace').split())


def available(profile='core'):
    """The required extensions this machine does not offer, as a tuple.

    An empty tuple means an offscreen context can be created.  No pbuffer or
    context is created, so an application can choose between offscreen
    rendering and a window before creating either.
    """
    try:
        offered = wgl_extensions()
    except WGLError:
        return REQUIRED_EXTENSIONS
    wanted = list(REQUIRED_EXTENSIONS)
    if profile != 'legacy':
        wanted.append(PROFILE_EXTENSION)
    return tuple(name for name in wanted if name not in offered)


# -- the offscreen context --------------------------------------------------

class OffscreenContext:
    """An OpenGL context rendering to a pbuffer, with no window on screen.

    The context is current after construction and after :meth:`make_current`.
    The pbuffer is the context's default framebuffer, so ``glReadPixels`` on
    framebuffer zero reads what was drawn.  Drawing code needs no changes for
    offscreen use.

    ``profile`` is one of :data:`PROFILES` and ``version`` is the requested GL
    version.  The remaining keyword arguments are those of
    :func:`pixel_format_attributes`.  If the driver cannot meet the request,
    the constructor raises :class:`WGLError` naming the step that failed.

    Release it with :meth:`release`, or use it as a context manager.
    """

    handle = None
    dc = None
    context = None
    pixel_format = None

    def __init__(self, width=256, height=256, profile='core', version=(3, 3),
                 debug=False, forward_compatible=False, share=None, **buffers):
        # Converted to int before the check, as in `resize`.  A width of 0.5
        # passes a `> 0` test and then makes a pbuffer zero pixels wide.
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise WGLError('cannot render at %dx%d' % (width, height))
        self.width, self.height = width, height
        self.profile = profile
        self.version = tuple(version)
        self._buffers = buffers
        missing = available(profile)
        if missing:
            raise WGLError(
                'this driver offers no offscreen OpenGL: %s missing'
                % (', '.join(missing),))
        try:
            with bootstrap().current():
                self.pixel_format = self._choose_pixel_format()
                self.handle, self.dc = self._create_pbuffer(
                    self.width, self.height)
                self.context = self._create_context(
                    debug, forward_compatible, share)
        except BaseException:
            # Release what was created, so an application that tries this and
            # falls back does not leak a pbuffer per attempt.
            self.release()
            raise
        self.make_current()

    # -- construction, one method per call that can fail --------------------

    def _choose_pixel_format(self):
        from OpenGL.raw.WGL._types import HDC
        from OpenGL.WGL.ARB import pixel_format

        attributes = pixel_format_attributes(**self._buffers)
        formats = (ctypes.c_int * 1)()
        found = ctypes.c_uint()
        chosen = pixel_format.wglChoosePixelFormatARB(
            HDC(bootstrap().dc), _ints(attributes), None, 1, formats,
            ctypes.byref(found),
        )
        if not chosen or not found.value:
            raise WGLError(
                'no pixel format can draw to a pbuffer with the buffers asked '
                'for (%s)' % (', '.join('%s=%r' % pair
                                        for pair in sorted(self._buffers.items()))
                              or 'the defaults',),
                ctypes.get_last_error(),
            )
        return formats[0]

    def _create_pbuffer(self, width, height):
        from OpenGL.raw.WGL._types import HDC
        from OpenGL.WGL.ARB import pbuffer

        handle = pbuffer.wglCreatePbufferARB(
            HDC(bootstrap().dc), self.pixel_format, width, height,
            _ints([0]),
        )
        if not handle:
            raise WGLError(
                'wglCreatePbufferARB failed for %dx%d; this driver renders at '
                'most %dx%d offscreen' % (
                    (width, height) + self.maximum_size()),
                ctypes.get_last_error(),
            )
        dc = pbuffer.wglGetPbufferDCARB(handle)
        if not dc:
            code = ctypes.get_last_error()
            pbuffer.wglDestroyPbufferARB(handle)
            raise WGLError('wglGetPbufferDCARB gave no device context', code)
        return handle, dc

    def _create_context(self, debug, forward_compatible, share):
        from OpenGL.raw.WGL._types import HDC, HGLRC
        from OpenGL.WGL.ARB import create_context

        attributes = context_attributes(
            profile=self.profile, version=self.version, debug=debug,
            forward_compatible=forward_compatible,
        )
        context = create_context.wglCreateContextAttribsARB(
            HDC(self.dc), HGLRC(share or 0), _ints(attributes),
        )
        if not context:
            major, minor = self.version
            raise WGLError(
                'wglCreateContextAttribsARB refused a %s-profile GL %d.%d '
                'context' % (self.profile, major, minor),
                ctypes.get_last_error(),
            )
        return context

    # -- use ----------------------------------------------------------------

    def make_current(self):
        """Bind this context and its pbuffer to the calling thread."""
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC, HGLRC

        if not WGL.wglMakeCurrent(HDC(self.dc), HGLRC(self.context)):
            raise WGLError('wglMakeCurrent for the offscreen context',
                           ctypes.get_last_error())

    def release_current(self):
        """Unbind whatever is current on the calling thread."""
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC, HGLRC

        WGL.wglMakeCurrent(HDC(0), HGLRC(0))

    def maximum_size(self):
        """The largest pbuffer this driver creates, as ``(width, height)``."""
        from OpenGL.raw.WGL._types import HDC
        from OpenGL.WGL.ARB import pbuffer, pixel_format

        wanted = _ints([pbuffer.WGL_MAX_PBUFFER_WIDTH_ARB,
                        pbuffer.WGL_MAX_PBUFFER_HEIGHT_ARB])
        values = (ctypes.c_int * 2)()
        if not pixel_format.wglGetPixelFormatAttribivARB(
            HDC(bootstrap().dc), self.pixel_format or 1, 0, 2, wanted, values
        ):
            return (0, 0)
        return (values[0], values[1])

    @property
    def lost(self):
        """True if the driver has discarded this pbuffer's contents.

        Windows may discard a pbuffer's contents on a display-mode change or a
        remote-desktop disconnect.  The pbuffer still exists at the same size.
        Redraw the frame; nothing needs to be recreated.
        """
        from OpenGL.WGL.ARB import pbuffer

        if self.handle is None:
            return False
        answer = ctypes.c_int()
        pbuffer.wglQueryPbufferARB(
            self.handle, pbuffer.WGL_PBUFFER_LOST_ARB, ctypes.byref(answer))
        return bool(answer.value)

    def resize(self, width, height):
        """Render at a new size.

        A pbuffer has a fixed size, so this creates a new pbuffer with the same
        pixel format and destroys the old one.  The GL context is kept, with
        its textures, buffers and programs, because a context can bind to any
        drawable with its pixel format.
        """
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise WGLError('cannot render at %dx%d' % (width, height))
        if (width, height) == (self.width, self.height):
            return
        with bootstrap().current():
            handle, dc = self._create_pbuffer(width, height)
        previous = (self.handle, self.dc)
        self.handle, self.dc = handle, dc
        try:
            self.make_current()
        except BaseException:
            self._release_pbuffer(*previous)
            raise
        self._release_pbuffer(*previous)
        self.width, self.height = width, height

    # -- teardown -----------------------------------------------------------

    def _release_pbuffer(self, handle, dc):
        from OpenGL.raw.WGL._types import HDC
        from OpenGL.WGL.ARB import pbuffer

        if handle is None:
            return
        if dc:
            pbuffer.wglReleasePbufferDCARB(handle, HDC(dc))
        pbuffer.wglDestroyPbufferARB(handle)

    def release(self, forget=True):
        """Destroy the context and the pbuffer.

        Safe to call part-way through construction, when some of these do not
        exist yet, and safe to call twice.

        ``wglDestroyPbufferARB`` refuses a pbuffer that is current on any
        thread.  It is also an extension entry point, which resolves only while
        a context is current.  The bootstrap context is therefore made current
        for the teardown.  That unbinds this context and lets the entry point
        resolve.

        With ``forget=True`` (the default), the context is removed from the
        dispatch layer.  The layer keeps a table of resolved entry points per
        context handle.  Without this, a handle the driver reuses would get the
        destroyed context's function pointers.  ``forget=False`` leaves that to
        a caller that manages the layer itself.  Examples are a caller retiring
        the tables of several contexts together, or a test reproducing a
        program that never calls ``forget_context``.
        """
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC, HGLRC

        if self.handle is None and self.context is None:
            return
        was_dc = WGL.wglGetCurrentDC()
        was_context = WGL.wglGetCurrentContext()
        # Restore the previous context only if it is a different context; this
        # one is being destroyed.
        restore = was_context and int(was_context) != int(self.context or 0)
        from OpenGL import _dispatch

        booted = bootstrap()
        WGL.wglMakeCurrent(HDC(booted.dc), HGLRC(booted.context))
        # Recorded whatever `forget` is, because the teardown below goes
        # through the dispatch layer.  ``wglReleasePbufferDCARB`` resolves in
        # the context the layer has recorded as current.  Without this call
        # that is the context being destroyed, whose table lacks the entry.
        _dispatch.make_current(booted.context)
        try:
            if self.context:
                if forget:
                    _dispatch.forget_context(self.context)
                WGL.wglDeleteContext(HGLRC(self.context))
                self.context = None
            self._release_pbuffer(self.handle, self.dc)
            self.handle = self.dc = None
        finally:
            WGL.wglMakeCurrent(
                HDC(was_dc or 0) if restore else HDC(0),
                HGLRC(was_context or 0) if restore else HGLRC(0),
            )
            # Record the restored context in the dispatch layer too.  Otherwise
            # the layer keeps using the bootstrap context's table, which has
            # almost no entries, and reports the caller's entry points as
            # undefined.
            _dispatch.make_current(was_context if restore else 0)

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.release()
        return False

    def __repr__(self):
        return '<%s %dx%d %s GL %d.%d>' % (
            self.__class__.__name__, self.width, self.height, self.profile,
            self.version[0], self.version[1])


@contextlib.contextmanager
def headless_context(width=256, height=256, **named):
    """An offscreen context, current for the body and then released.

    A shorthand for :class:`OffscreenContext`, matching
    ``OpenGL.CGL.headless_context``::

        with headless_context(64, 48) as context:
            glClear(GL_COLOR_BUFFER_BIT)
            pixels = glReadPixels(0, 0, 64, 48, GL_RGB, GL_UNSIGNED_BYTE)
    """
    context = OffscreenContext(width=width, height=height, **named)
    try:
        yield context
    finally:
        context.release()
