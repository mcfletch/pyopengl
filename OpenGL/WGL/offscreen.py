"""Offscreen OpenGL on Windows: a context with nothing on screen.

WGL binds a rendering context to a *device context*, and Windows hands out
device contexts for things it can draw on.  There is no "give me a context on
this adapter" call to make, as EGL has, and no windowless context, as CGL has.
What Windows offers instead is the **pbuffer**: a drawable the driver allocates
out of its own memory, with a device context of its own that belongs to no
window and appears nowhere.  That is what this module renders on::

    from OpenGL.WGL.offscreen import headless_context

    with headless_context(width=640, height=480) as context:
        ...                                 # the context is current here

A pbuffer *is* the default framebuffer, so ``glClear``, ``glReadPixels`` and a
screenshot behave exactly as they do on a window and nothing drawing into it
has to know where it is.  (CGL's headless context differs here: it has no
default framebuffer at all and needs a framebuffer object bound before
anything can be drawn.)

**One window is created and never shown.**  The calls that make all of this
possible -- ``wglChoosePixelFormatARB``, ``wglCreatePbufferARB``,
``wglCreateContextAttribsARB`` -- are WGL extensions, and an extension entry
point is resolved through ``wglGetProcAddress``, which answers only while a
context is current.  So there is a chicken and egg, and Windows gives one way
out of it: a window, a pixel format on its device context, and an OpenGL 1.1
context on that, used for nothing but resolving the entry points that build the
real thing.  :func:`bootstrap` creates one of those per process, sized 1x1,
``WS_POPUP``, never shown and never given to a message loop.  The pbuffer
outlives it and is not tied to it.

What that costs is a window station and a desktop, which a service running in
session 0 has.  What it does not need is anything on screen, a compositor, a
logged-in session, or a remote-desktop connection that stays open.

**Where this works.**  ``WGL_ARB_pbuffer``, ``WGL_ARB_pixel_format`` and
``WGL_ARB_create_context`` are what a driver has to offer, and every hardware
OpenGL driver for Windows has offered them since about 2009.  Microsoft's own
fallback rasteriser -- the GDI generic implementation, which is what a machine
with no vendor driver installed has -- offers none of them and is OpenGL 1.1
besides.  :func:`available` answers whether this machine can render offscreen,
and construction raises :class:`WGLError` naming what is missing rather than
failing obscurely, so an application can try it and fall back.

The Mesa and ANGLE builds shipped for Windows provide EGL instead, and
``OpenGL.EGL`` reaches those; ANGLE offers OpenGL ES rather than desktop GL.
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
    """A WGL or Win32 call failed, or the machine cannot serve the request.

    ``operation`` names the call and ``code`` is the ``GetLastError`` value
    where there was one, so a caller can tell "this driver has no pbuffers"
    from "the size asked for was too large" without reading the message.
    """

    def __init__(self, operation, code=0):
        self.operation = operation
        self.code = code
        if code:
            super().__init__('%s (Windows error %d)' % (operation, code))
        else:
            super().__init__(operation)


# -- the Win32 surface this needs ------------------------------------------
#
# Declared here rather than reached for through a wrapper package: PyOpenGL
# depends on nothing but ctypes, and this is eight functions.
#
# In plain ctypes types rather than ``ctypes.wintypes``, and loaded on use
# rather than at import, so that this module imports on any platform and the
# half of it that only builds attribute lists can be read and tested from one.
# A handle is ``c_void_p``: Windows documents USER and GDI handles as 32-bit
# values sign-extended to 64 bits, so half of the real ones have their top
# half set and anything narrower loses it.

_HANDLE = ctypes.c_void_p
_DWORD = ctypes.c_uint32
_WORD = ctypes.c_uint16


class PIXELFORMATDESCRIPTOR(ctypes.Structure):
    """What ``ChoosePixelFormat`` and ``SetPixelFormat`` describe a format with.

    Only the bootstrap window needs one: the pbuffer's format is chosen by
    :func:`pixel_format_attributes` through ``wglChoosePixelFormatARB``, which
    is the call that can express "must be able to draw to a pbuffer" at all.
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

    ``lpfnWndProc`` is a plain pointer here and is filled with the address of
    ``DefWindowProcW``: the window handles no messages of its own, so there is
    no Python callback to declare a prototype for -- and none to keep alive.
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

    Raises :class:`WGLError` rather than ``AttributeError`` off a platform
    with no ``ctypes.WinDLL``, so a caller that reached here by accident is
    told what it reached for.
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

#: ``CS_OWNDC``: the window keeps its own device context rather than borrowing
#: one from a pool.  A pixel format is set on a device context and stays set,
#: so a borrowed one loses it the moment it is returned.
_CS_OWNDC = 0x0020

#: ``WS_POPUP``: no frame, no caption, no parent, and -- with ``WS_VISIBLE``
#: left off -- nothing on screen.
_WS_POPUP = 0x80000000

_PFD_DRAW_TO_WINDOW = 0x00000004
_PFD_SUPPORT_OPENGL = 0x00000020
_PFD_TYPE_RGBA = 0

#: ``ERROR_CLASS_ALREADY_EXISTS`` from ``RegisterClass``, which is not a
#: failure: the class this process wanted is there.
_ERROR_CLASS_ALREADY_EXISTS = 1410

#: The class the bootstrap window is registered under.  Registration is
#: per-module-instance, so the name has to be one nothing else will take.
_WINDOW_CLASS = 'PyOpenGLOffscreenBootstrap'


# -- what a request may ask for --------------------------------------------

#: The context profiles ``wglCreateContextAttribsARB`` offers, by the name this
#: module takes for them.  ``'legacy'`` asks for no profile at all, which is
#: what a driver answers with its own default and the only choice below GL 3.2.
PROFILES = ('core', 'compatibility', 'legacy')

#: Whether the pixel format has to be one the GPU draws.  ``'accelerated'`` is
#: what anything caring about speed wants; ``'any'`` lets the driver answer
#: with whatever it has, which is what a machine with an unusual or virtualised
#: adapter may need.
ACCELERATION_KINDS = ('accelerated', 'any')

#: The extensions an offscreen context is built from.  A driver missing any of
#: them cannot serve one, and :func:`available` says so by name.
REQUIRED_EXTENSIONS = (
    'WGL_ARB_pixel_format',
    'WGL_ARB_pbuffer',
    'WGL_ARB_create_context',
)

#: Additionally required to ask for a named profile.  Without it the only
#: context available is the driver's default, which is ``'legacy'``.
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

    Pure, so what a caller asked for can be read off without a Windows machine
    to ask.  The sizes are bits per buffer, ``color_bits`` counting the three
    colour channels together as WGL does.  A size of zero or less is left out
    rather than requested as zero, so the driver picks.

    ``WGL_DRAW_TO_PBUFFER_ARB`` is always requested and is the point of the
    list: it is the one thing the old ``ChoosePixelFormat`` cannot express, and
    a format without it produces a pbuffer the driver refuses to create.

    The list is terminated with a zero, which is how WGL knows where it ends.
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
        # Asked for explicitly rather than left to the driver: a format is a
        # match if it is *at least* what was asked for, and single-buffered is
        # what an offscreen surface wants -- there is nothing to present to,
        # and a back buffer nobody swaps is memory spent on nothing.
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

    Pure, as :func:`pixel_format_attributes` is.  ``profile`` is one of
    :data:`PROFILES`; ``'legacy'`` names no profile bit, which is what a
    request below GL 3.2 must do -- the profile mask did not exist there, and a
    driver handed one refuses the whole request.
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

    One per process, from :func:`bootstrap`.  It exists because the calls that
    build an offscreen context are extensions, and an extension entry point can
    only be resolved while some context is current.  Nothing is ever drawn
    through it.
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
            # ERROR_CLASS_ALREADY_EXISTS, which is what a second interpreter in
            # the same process -- or a reloaded module -- meets.
            if code != _ERROR_CLASS_ALREADY_EXISTS:
                raise WGLError('RegisterClass for the bootstrap window', code)
        # Kept for the life of the process: Windows reads the class out of
        # this structure for as long as it is registered.
        cls._declaration = declaration
        cls._instance = instance

    def _set_pixel_format(self):
        """Any format that supports OpenGL will do; nothing is drawn on it."""
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
        """Make the bootstrap context current for the body, then put back what
        was current before.

        Restoring matters: an application that already had a context of its own
        current when it asked for an offscreen one must not find that context
        quietly replaced.
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
        """Give back the window, its device context and the GL context."""
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

    Shared rather than made per context: a pbuffer's device is named by the
    device context passed to ``wglCreatePbufferARB`` and its buffers by the
    pixel format passed beside it, so one window serves every offscreen context
    on the machine.
    """
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = _Bootstrap()
    return _bootstrap


def release_bootstrap():
    """Let go of the bootstrap window, if one was built.

    Nothing needs to call this -- one hidden 1x1 window and an OpenGL 1.1
    context cost almost nothing and the process is going to end -- but a test
    that wants to prove the bootstrap rebuilds itself, or an application
    unloading a plug-in, can.  Offscreen contexts already made are unaffected:
    a pbuffer is not tied to the window it was created through.
    """
    global _bootstrap
    if _bootstrap is not None:
        _bootstrap.release()
        _bootstrap = None


def wgl_extensions():
    """The WGL extension names this machine offers, as a frozenset.

    Empty where the string cannot be read at all, which is what the GDI generic
    implementation gives: it exports no ``wglGetExtensionsStringARB``.
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
    """What is missing before an offscreen context can be made, or ``()``.

    Returns the names of the required extensions this machine does not offer,
    so an empty result means yes.  Answers without creating a pbuffer or a
    context, which is what lets an application decide between this and a window
    before committing to either.
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

    Created current, and current again after :meth:`make_current`.  The pbuffer
    is the context's default framebuffer, so ``glReadPixels`` against
    framebuffer zero reads what was drawn and nothing has to be told it is
    offscreen.

    ``profile`` is one of :data:`PROFILES` and ``version`` the GL version
    asked for; the remaining keyword arguments are
    :func:`pixel_format_attributes`'.  A driver that cannot serve the request
    raises :class:`WGLError` naming what it could not do.

    Release it with :meth:`release`, or use it as a context manager.
    """

    handle = None
    dc = None
    context = None
    pixel_format = None

    def __init__(self, width=256, height=256, profile='core', version=(3, 3),
                 debug=False, forward_compatible=False, share=None, **buffers):
        # Rounded before it is judged, as `resize` does: a width of 0.5 passes
        # a `> 0` test and then makes a pbuffer no pixels wide.
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
            # Part-way construction leaks a pbuffer per attempt otherwise, and
            # an application is invited to try this and fall back.
            self.release()
            raise
        self.make_current()

    # -- construction, one step per call that can fail ----------------------

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

    # -- using it -----------------------------------------------------------

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
        """``(width, height)`` -- the largest pbuffer this driver will make."""
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
        """Whether the driver has taken this pbuffer's memory back.

        Windows may discard a pbuffer's contents on a display-mode change or a
        remote-desktop disconnect.  The pbuffer is still there and still the
        right size; what it held is gone, so the answer is to draw the frame
        again rather than to rebuild anything.
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

        A pbuffer is created at a fixed size and cannot be resized, so this
        builds a replacement on the same pixel format and drops the old one.
        The GL context survives -- textures, buffers and programs are all still
        there afterwards -- because a context binds to any drawable sharing its
        format.
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

    # -- letting go ---------------------------------------------------------

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

        Written to be callable part-way through construction, where some of
        them do not exist yet, and harmless to call twice.

        The order is what the two rules leave: ``wglDestroyPbufferARB`` refuses
        a pbuffer that is current to any thread, and it is itself an extension
        entry point, which resolves only while *some* context is current.  So
        the bootstrap context takes over for the teardown -- it unbinds this
        one and answers for the resolution at the same time.

        The dispatch layer is told the context has gone: it keeps a table of
        resolved entry points per context handle, and a handle the driver hands
        out again would otherwise arrive with the dead context's function
        pointers already in it.  ``forget=False`` leaves that to the caller,
        which is for a caller that manages the layer itself -- one holding
        several contexts and retiring their tables together, or one
        reproducing what a program that never notifies PyOpenGL actually
        faces.  A caller that simply wants the context gone wants the default.
        """
        from OpenGL import WGL
        from OpenGL.raw.WGL._types import HDC, HGLRC

        if self.handle is None and self.context is None:
            return
        was_dc = WGL.wglGetCurrentDC()
        was_context = WGL.wglGetCurrentContext()
        # Only worth putting back if it belongs to somebody else; this one is
        # about to stop existing.
        restore = was_context and int(was_context) != int(self.context or 0)
        from OpenGL import _dispatch

        booted = bootstrap()
        WGL.wglMakeCurrent(HDC(booted.dc), HGLRC(booted.context))
        # Said whatever `forget` asks, because the teardown below is itself
        # dispatched: ``wglReleasePbufferDCARB`` has to resolve, and it
        # resolves in whichever context the layer believes is current.  Left
        # unsaid, that is the context being destroyed, whose table does not
        # have it.
        _dispatch.make_current(int(booted.context or 0))
        try:
            if self.context:
                if forget:
                    _dispatch.forget_context(int(self.context))
                WGL.wglDeleteContext(HGLRC(self.context))
                self.context = None
            self._release_pbuffer(self.handle, self.dc)
            self.handle = self.dc = None
        finally:
            WGL.wglMakeCurrent(
                HDC(was_dc or 0) if restore else HDC(0),
                HGLRC(was_context or 0) if restore else HGLRC(0),
            )
            # And say so, since the bootstrap was named above: left standing,
            # the layer goes on dispatching through the bootstrap's table -- a
            # legacy context that has resolved almost nothing -- and reports
            # entry points the caller's own context had as undefined.
            _dispatch.make_current(int(was_context or 0) if restore else 0)

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

    The convenience form of :class:`OffscreenContext`, and the counterpart of
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
