"""CGL, the macOS interface that creates OpenGL contexts without a window.

CGL (Core OpenGL) is the lowest-level OpenGL interface on macOS.  NSGL is built
on it: `NSOpenGLContext
<https://developer.apple.com/documentation/appkit/nsopenglcontext>`__ and
``NSOpenGLPixelFormat`` in AppKit, the Cocoa framework macOS applications make
their windows with, and the interface GUI toolkits use to give a window an
OpenGL context.  CGL creates a context with no window and no window server, for
offscreen rendering::

    from OpenGL.CGL import headless_context

    with headless_context() as context:
        ...                                 # the context is current here

PyOpenGL's test suite renders into a context made here on macOS
(``TEST_WINDOWING=cgl``).  :mod:`OpenGL.Tk` on Aqua makes its context through
NSGL, with the pixel format and profile chosen by this module.

**There is no default framebuffer.**  Framebuffer zero belongs to a drawable,
and a context created this way has none: a ``glClear`` or a ``glReadPixels``
against it draws nowhere and reads nothing.  Render into a framebuffer object
instead -- :func:`headless_context` is the context alone, and
:class:`OffscreenTarget` is a colour/depth/stencil target to bind to it.

**Which renderer answers is a choice.**  A machine with no accelerated renderer
available -- a virtual machine, or a session with no window server -- has only
Apple's CPU renderer, and asking for acceleration there fails rather than
falling back.  :func:`pixel_format_attributes` builds the attribute list for
either, and :func:`choose_pixel_format` tries acceleration first and settles for
what is on offer, reporting which it got.

Constant values are from Apple's ``CGLTypes.h`` and ``CGLRenderers.h``.
"""

import contextlib
import ctypes
import re

__all__ = (
    'CGL_ERROR_NAMES',
    'MAX_VERSION',
    'PROFILES',
    'PROFILE_VERSIONS',
    'RENDERER_KINDS',
    'RENDERER_ORDER',
    'CGLError',
    'OffscreenTarget',
    'RendererInfo',
    'choose_pixel_format',
    'headless_context',
    'parse_gl_version',
    'pixel_format_attributes',
    'pixel_format_candidates',
    'profile_for',
    'renderers',
    'set_swap_interval',
    'version_shortfall',
)

# -- types -----------------------------------------------------------------

CGLPixelFormatObj = ctypes.c_void_p
CGLContextObj = ctypes.c_void_p
CGLPixelFormatAttribute = ctypes.c_uint32
GLint = ctypes.c_int32

# -- pixel format attributes (CGLTypes.h) ----------------------------------

kCGLPFAAllRenderers = 1
kCGLPFATripleBuffer = 3
kCGLPFADoubleBuffer = 5
kCGLPFAStereo = 6
kCGLPFAAuxBuffers = 7
kCGLPFAColorSize = 8
kCGLPFAAlphaSize = 11
kCGLPFADepthSize = 12
kCGLPFAStencilSize = 13
kCGLPFAAccumSize = 14
kCGLPFAMinimumPolicy = 51
kCGLPFAMaximumPolicy = 52
kCGLPFASampleBuffers = 55
kCGLPFASamples = 56
kCGLPFAAuxDepthStencil = 57
kCGLPFAColorFloat = 58
kCGLPFAMultisample = 59
kCGLPFASupersample = 60
kCGLPFASampleAlpha = 61
kCGLPFARendererID = 70
kCGLPFASingleRenderer = 71
kCGLPFANoRecovery = 72
kCGLPFAAccelerated = 73
kCGLPFAClosestPolicy = 74
kCGLPFABackingStore = 76
kCGLPFABackingVolatile = 77
kCGLPFADisplayMask = 84
kCGLPFAAllowOfflineRenderers = 96
kCGLPFAAcceleratedCompute = 97
kCGLPFAOpenGLProfile = 99
kCGLPFASupportsAutomaticGraphicsSwitching = 101
kCGLPFAVirtualScreenCount = 128

# -- context parameters (CGLTypes.h) -----------------------------------------

kCGLCPSwapInterval = 222

# -- OpenGL profiles (CGLTypes.h) ------------------------------------------

kCGLOGLPVersion_Legacy = 0x1000
kCGLOGLPVersion_3_2_Core = 0x3200
kCGLOGLPVersion_GL3_Core = 0x3200
kCGLOGLPVersion_GL4_Core = 0x4100

#: The profiles CGL offers, by the name this module takes for them.  macOS has
#: no compatibility profile above 2.1: ``'legacy'`` is the fixed-function
#: pipeline at GL 2.1, and the two core profiles have no fixed function in them
#: at all.
PROFILES = {
    'legacy': kCGLOGLPVersion_Legacy,
    'core3': kCGLOGLPVersion_3_2_Core,
    'core4': kCGLOGLPVersion_GL4_Core,
}

#: The GL version each profile promises.  Worth comparing against what the
#: context reports: CGL accepts a pixel format naming a profile the renderer
#: cannot provide and hands back a lower context rather than refusing, and
#: macOS resolves every entry point from the framework whether or not the
#: current context implements it -- so a call the context does not have
#: segfaults instead of failing.
PROFILE_VERSIONS = {
    'legacy': (2, 1),
    'core3': (3, 2),
    'core4': (4, 1),
}

#: The highest GL version macOS provides.  A pixel format naming the 4.1 core
#: profile is the most it can be asked for; there is no 4.2 to ask for.
MAX_VERSION = (4, 1)

#: The lowest GL version each CGL profile provides, highest first.  macOS
#: answers a request for 3.2 or above with a core profile and has no
#: compatibility one there; the legacy profile is 2.1 and is the only one with
#: fixed function in it.
_PROFILE_FLOORS = (
    ((4, 1), 'core4'),
    ((3, 2), 'core3'),
    ((0, 0), 'legacy'),
)

_ES_APIS = ('gles', 'es')


def profile_for(api, profile, gl_version):
    """The CGL profile serving this request, or ``None`` with the reason why.

    Returns ``(profile_name, None)`` or ``(None, reason)``, ``profile_name``
    being a key of :data:`PROFILES`.  ``api`` is ``'gl'`` or ``'gles'``,
    ``profile`` is ``'core'`` or ``'compatibility'`` and ``gl_version`` is a
    ``(major, minor)`` pair.  Pure, so what macOS will and will not serve is
    readable without a Mac: the two refusals are OpenGL-ES, which CGL does not
    provide at all, and a compatibility profile above 2.1, which macOS does
    not have.
    """
    if (api or 'gl').lower() in _ES_APIS:
        return None, 'CGL provides no OpenGL-ES contexts'
    major, minor = gl_version
    wants_core = (profile or 'compatibility').lower() == 'core'
    if not wants_core and (major, minor) > (2, 1):
        return None, (
            'macOS has no compatibility profile above 2.1; %d.%d was asked for'
            % (major, minor))
    if not wants_core:
        return 'legacy', None
    for floor, name in _PROFILE_FLOORS:
        if (major, minor) >= floor:
            if name == 'legacy':
                return None, (
                    'a core profile below 3.2 does not exist; %d.%d was asked '
                    'for' % (major, minor))
            return name, None
    return None, 'no CGL profile for %d.%d' % (major, minor)   # pragma: no cover


#: The leading ``major.minor`` of a ``GL_VERSION`` string, past any API name.
#: Desktop GL starts with the number; OpenGL-ES puts "OpenGL ES" (or
#: "OpenGL ES-CM") in front of it.
_VERSION = re.compile(r'(?:OpenGL\s+ES(?:-CM|-SC)?\s+)?(\d+)\.(\d+)')


def parse_gl_version(reported):
    """``(major, minor)`` from a ``GL_VERSION`` string, or ``None``.

    Everything after the number is the driver describing itself and differs by
    vendor, so only the front is read.
    """
    if not reported:
        return None
    found = _VERSION.match(reported.strip())
    if not found:
        return None
    return (int(found.group(1)), int(found.group(2)))


def version_shortfall(reported, wanted):
    """Why ``reported`` does not meet ``wanted``, or ``None`` where it does.

    Asking for a version is not getting it.  GLFW refuses a request its driver
    cannot meet, so a window either has the version or was never made; CGL
    accepts a pixel format naming the 3.2 core profile on a renderer that
    implements 2.1 and hands back a 2.1 context.

    That gap is not a failed test but a dead process: macOS exports every entry
    point from the framework whether or not the current context implements it,
    so a GL 3.1 call on a 2.1 context resolves, is called, and segfaults.

    A version this cannot read is let through.  Refusing there would turn one
    unrecognised driver string into a skip on every test it runs, and the entry
    points still answer for themselves.
    """
    if not wanted:
        return None
    found = parse_gl_version(reported)
    if found is None or found >= tuple(wanted):
        return None
    return ('the context provides GL %d.%d, short of the %d.%d asked for'
            % (found + tuple(wanted)))


# -- renderer ids (CGLRenderers.h) -----------------------------------------

kCGLRendererGenericID = 0x00020200
kCGLRendererGenericFloatID = 0x00020400
kCGLRendererAppleSWID = 0x00020600
kCGLRendererIDMatchingMask = 0x00FE7F00

#: How to ask for a kind of renderer, by the name this module takes for it.
#: ``'any'`` names no preference, which is what a machine with no accelerated
#: renderer needs: asking for acceleration where there is none fails outright
#: rather than falling back.
RENDERER_KINDS = ('accelerated', 'any', 'software')

# -- renderer properties (CGLTypes.h) --------------------------------------
#
# CGLQueryRendererInfo describes what this machine can render *without*
# creating anything, which is the only way to know what a context would have
# been before asking for one.

kCGLRPOffScreen = 53
kCGLRPFullScreen = 54
kCGLRPRendererID = 70
kCGLRPAccelerated = 73
kCGLRPRobust = 75
kCGLRPBackingStore = 76
kCGLRPMPSafe = 78
kCGLRPWindow = 80
kCGLRPMultiScreen = 81
kCGLRPCompliant = 83
kCGLRPDisplayMask = 84
kCGLRPBufferModes = 100
kCGLRPColorModes = 103
kCGLRPAccumModes = 104
kCGLRPDepthModes = 105
kCGLRPStencilModes = 106
kCGLRPMaxAuxBuffers = 107
kCGLRPMaxSampleBuffers = 108
kCGLRPMaxSamples = 109
kCGLRPSampleModes = 110
kCGLRPSampleAlpha = 111
kCGLRPGPUVertProcCapable = 122
kCGLRPGPUFragProcCapable = 123
kCGLRPRendererCount = 128
kCGLRPOnline = 129
kCGLRPAcceleratedCompute = 130
kCGLRPVideoMemoryMegabytes = 131
kCGLRPTextureMemoryMegabytes = 132
kCGLRPMajorGLVersion = 133
kCGLRPRegistryIDLow = 140
kCGLRPRegistryIDHigh = 141
kCGLRPRemovable = 142

#: Query every renderer, whatever display it belongs to.
kCGLDisplayMaskAll = 0xFFFFFFFF


class RendererInfo:
    """One renderer this machine offers, and what it can do.

    ``major_gl_version`` is the highest GL major version it supports, which is
    what decides whether a core profile asked of it will be the profile that
    comes back: CGL accepts a pixel format naming one this renderer cannot
    provide and answers with a lower context rather than refusing.
    """

    __slots__ = ('accelerated', 'index', 'major_gl_version', 'online',
                 'renderer_id', 'video_memory')

    def __init__(self, index, renderer_id, accelerated, online,
                 major_gl_version, video_memory):
        self.index = index
        self.renderer_id = renderer_id
        self.accelerated = bool(accelerated)
        self.online = bool(online)
        self.major_gl_version = major_gl_version
        self.video_memory = video_memory

    @property
    def software(self):
        """Whether this renderer rasterises on the CPU."""
        return not self.accelerated

    def __repr__(self):
        return '<%s %d id=0x%08X %s, GL %s, %s MB>' % (
            self.__class__.__name__, self.index, self.renderer_id,
            'software' if self.software else 'accelerated',
            self.major_gl_version, self.video_memory)


def renderers(display_mask=kCGLDisplayMaskAll):
    """Every renderer this machine offers, as :class:`RendererInfo`.

    Creates no context and opens no window, so it answers on a machine where
    nothing else here would -- which is what makes it the first thing to ask
    when a context turns out not to be what was requested.
    """
    cgl = library()
    info = ctypes.c_void_p()
    count = GLint()
    _check('CGLQueryRendererInfo',
           cgl.CGLQueryRendererInfo(display_mask, ctypes.byref(info),
                                    ctypes.byref(count)))
    try:
        found = []
        for index in range(count.value):
            def describe(prop, _index=index):
                value = GLint()
                if cgl.CGLDescribeRenderer(info, _index, prop,
                                           ctypes.byref(value)) != 0:
                    return 0
                return value.value

            found.append(RendererInfo(
                index=index,
                renderer_id=describe(kCGLRPRendererID),
                accelerated=describe(kCGLRPAccelerated),
                online=describe(kCGLRPOnline),
                major_gl_version=describe(kCGLRPMajorGLVersion),
                video_memory=describe(kCGLRPVideoMemoryMegabytes),
            ))
        return tuple(found)
    finally:
        cgl.CGLDestroyRendererInfo(info)


# -- errors (CGLTypes.h) ---------------------------------------------------

CGL_ERROR_NAMES = {
    0: 'kCGLNoError',
    10000: 'kCGLBadAttribute',
    10001: 'kCGLBadProperty',
    10002: 'kCGLBadPixelFormat',
    10003: 'kCGLBadRendererInfo',
    10004: 'kCGLBadContext',
    10005: 'kCGLBadDrawable',
    10006: 'kCGLBadDisplay',
    10007: 'kCGLBadState',
    10008: 'kCGLBadValue',
    10009: 'kCGLBadMatch',
    10010: 'kCGLBadEnumeration',
    10011: 'kCGLBadOffScreen',
    10012: 'kCGLBadFullScreen',
    10013: 'kCGLBadWindow',
    10014: 'kCGLBadAddress',
    10015: 'kCGLBadCodeModule',
    10016: 'kCGLBadAlloc',
    10017: 'kCGLBadConnection',
}


class CGLError(RuntimeError):
    """A CGL call answered with an error.

    ``code`` is the ``CGLError`` value and ``operation`` the call that returned
    it, so a caller can tell "this machine offers no such pixel format" from
    "the arguments were wrong" without parsing the message.
    """

    def __init__(self, operation, code):
        self.operation = operation
        self.code = code
        super().__init__('%s: %s (%s)' % (
            operation, CGL_ERROR_NAMES.get(code, 'unknown CGL error'), code))


# -- the library -----------------------------------------------------------

_cgl = None


def library():
    """The OpenGL framework, with the CGL entry points declared.

    Loaded on use rather than at import, so this module can be imported --
    and its attribute-building half used and tested -- on a platform that has
    no CGL at all.
    """
    global _cgl
    if _cgl is None:
        from OpenGL.platform import PLATFORM

        cgl = getattr(PLATFORM, 'CGL', None)
        if cgl is None:
            raise CGLError('loading CGL', 10006)    # kCGLBadDisplay
        cgl.CGLChoosePixelFormat.argtypes = [
            ctypes.POINTER(CGLPixelFormatAttribute),
            ctypes.POINTER(CGLPixelFormatObj),
            ctypes.POINTER(GLint),
        ]
        cgl.CGLChoosePixelFormat.restype = ctypes.c_int32
        cgl.CGLDestroyPixelFormat.argtypes = [CGLPixelFormatObj]
        cgl.CGLDestroyPixelFormat.restype = ctypes.c_int32
        cgl.CGLCreateContext.argtypes = [
            CGLPixelFormatObj, CGLContextObj, ctypes.POINTER(CGLContextObj),
        ]
        cgl.CGLCreateContext.restype = ctypes.c_int32
        cgl.CGLDestroyContext.argtypes = [CGLContextObj]
        cgl.CGLDestroyContext.restype = ctypes.c_int32
        cgl.CGLSetCurrentContext.argtypes = [CGLContextObj]
        cgl.CGLSetCurrentContext.restype = ctypes.c_int32
        cgl.CGLGetCurrentContext.argtypes = []
        cgl.CGLGetCurrentContext.restype = CGLContextObj
        cgl.CGLSetParameter.argtypes = [
            CGLContextObj, ctypes.c_int32, ctypes.POINTER(GLint),
        ]
        cgl.CGLSetParameter.restype = ctypes.c_int32
        cgl.CGLDescribePixelFormat.argtypes = [
            CGLPixelFormatObj, GLint, CGLPixelFormatAttribute,
            ctypes.POINTER(GLint),
        ]
        cgl.CGLDescribePixelFormat.restype = ctypes.c_int32
        cgl.CGLQueryRendererInfo.argtypes = [
            ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(GLint),
        ]
        cgl.CGLQueryRendererInfo.restype = ctypes.c_int32
        cgl.CGLDescribeRenderer.argtypes = [
            ctypes.c_void_p, GLint, ctypes.c_uint32, ctypes.POINTER(GLint),
        ]
        cgl.CGLDescribeRenderer.restype = ctypes.c_int32
        cgl.CGLDestroyRendererInfo.argtypes = [ctypes.c_void_p]
        cgl.CGLDestroyRendererInfo.restype = ctypes.c_int32
        _cgl = cgl
    return _cgl


def _check(operation, code):
    if code != 0:
        raise CGLError(operation, code)
    return code


# -- choosing a pixel format -----------------------------------------------

def pixel_format_attributes(profile='legacy', renderer='accelerated',
                            color_size=24, alpha_size=8, depth_size=24,
                            stencil_size=8, samples=0, double_buffer=False,
                            stereo=False):
    """The attribute list ``CGLChoosePixelFormat`` takes, as plain integers.

    Pure, so what a caller asked for can be read off without a Mac to ask.
    ``profile`` is a key of :data:`PROFILES` and ``renderer`` one of
    :data:`RENDERER_KINDS`; the sizes are bits per buffer, ``color_size``
    counting the three colour channels together as CGL does.  ``stereo`` asks
    for a stereo pair of colour buffers, which few renderers offer.

    The list is terminated with a zero, which is how CGL knows where it ends.
    """
    if profile not in PROFILES:
        raise ValueError('profile must be one of %r, not %r'
                         % (sorted(PROFILES), profile))
    if renderer not in RENDERER_KINDS:
        raise ValueError('renderer must be one of %r, not %r'
                         % (list(RENDERER_KINDS), renderer))
    attributes = [kCGLPFAOpenGLProfile, PROFILES[profile]]
    if renderer == 'accelerated':
        attributes.append(kCGLPFAAccelerated)
    elif renderer == 'software':
        # Naming the renderer is the only way to *ask for* the CPU one; there
        # is no "not accelerated" attribute.
        attributes += [kCGLPFARendererID, kCGLRendererGenericFloatID]
    # 'any' names neither, and lets CGL answer with whatever it has.
    if double_buffer:
        attributes.append(kCGLPFADoubleBuffer)
    if stereo:
        attributes.append(kCGLPFAStereo)
    attributes += [
        kCGLPFAColorSize, color_size,
        kCGLPFAAlphaSize, alpha_size,
        kCGLPFADepthSize, depth_size,
        kCGLPFAStencilSize, stencil_size,
    ]
    if samples:
        attributes += [kCGLPFASampleBuffers, 1, kCGLPFASamples, samples]
    attributes.append(0)
    return attributes


#: The renderer kinds tried in turn when none is named.  A GPU is worth having
#: where there is one; 'any' is what answers on a machine whose only renderer
#: is Apple's CPU one but which does not advertise it under the generic-float
#: id; naming that id is the last resort.
RENDERER_ORDER = ('accelerated', 'any', 'software')


def pixel_format_candidates(profile='legacy', renderer=None, **sizes):
    """The pixel formats to try, as ``(renderer_kind, attribute_array)`` pairs.

    With ``renderer`` given, that kind is the only one offered.  Without, the
    kinds in :data:`RENDERER_ORDER` are, so the first that the machine can
    serve is the one to take.  Each array is a ctypes array of
    ``CGLPixelFormatAttribute`` ending in zero, which is what both
    ``CGLChoosePixelFormat`` and ``NSOpenGLPixelFormat`` take; ``sizes`` are
    :func:`pixel_format_attributes`'.
    """
    kinds = (renderer,) if renderer is not None else RENDERER_ORDER
    for kind in kinds:
        attributes = pixel_format_attributes(
            profile=profile, renderer=kind, **sizes)
        yield kind, (CGLPixelFormatAttribute * len(attributes))(*attributes)


def choose_pixel_format(profile='legacy', renderer=None, **sizes):
    """A pixel format for this machine, and the renderer kind it came from.

    Returns ``(pixel_format, renderer_kind)``, taking the first of
    :func:`pixel_format_candidates` the machine offers -- so a Mac with a GPU
    renders on it, and a virtual machine or a session with no window server
    still gets a context instead of an error.

    Raises :class:`CGLError` if none of them is available.
    """
    cgl = library()
    failure = None
    for kind, array in pixel_format_candidates(profile, renderer, **sizes):
        pixel_format = CGLPixelFormatObj()
        count = GLint()
        code = cgl.CGLChoosePixelFormat(
            array, ctypes.byref(pixel_format), ctypes.byref(count))
        if code == 0 and pixel_format.value and count.value > 0:
            return pixel_format, kind
        failure = failure or CGLError('CGLChoosePixelFormat', code or 10002)
    raise failure


def set_swap_interval(context, interval):
    """Wait ``interval`` display refreshes between buffer swaps; True if set.

    ``context`` is a ``CGLContextObj``.  Zero swaps as fast as the renderer
    will, which is what a benchmark wants.  False where the renderer refuses
    the parameter.
    """
    value = GLint(int(interval))
    return library().CGLSetParameter(
        context, kCGLCPSwapInterval, ctypes.byref(value)) == 0


# -- a context ---------------------------------------------------------------

@contextlib.contextmanager
def headless_context(profile='legacy', renderer=None, **sizes):
    """A CGL context with no drawable, current for the body and then destroyed.

    Yields the ``CGLContextObj``.  ``profile`` is a key of :data:`PROFILES`;
    the remaining arguments are :func:`pixel_format_attributes`'.  Remember
    that there is no default framebuffer: bind an :class:`OffscreenTarget`
    before drawing anything.
    """
    cgl = library()
    pixel_format = choose_pixel_format(
        profile=profile, renderer=renderer, **sizes)[0]
    context = CGLContextObj()
    try:
        _check('CGLCreateContext',
               cgl.CGLCreateContext(pixel_format, None, ctypes.byref(context)))
    finally:
        cgl.CGLDestroyPixelFormat(pixel_format)
    try:
        _check('CGLSetCurrentContext', cgl.CGLSetCurrentContext(context))
        yield context
    finally:
        cgl.CGLSetCurrentContext(None)
        cgl.CGLDestroyContext(context)


class OffscreenTarget:
    """A framebuffer object to draw into, since there is no framebuffer zero.

    Built and bound inside a current context, and torn down with
    :meth:`release`.  ``color_format`` is the colour attachment's internal
    format, ``GL_RGBA8`` unless a caller wants something else -- ``GL_RGB8``
    for a target whose readback should have no alpha in it -- and the
    depth/stencil attachment is ``GL_DEPTH24_STENCIL8``.  ``glReadPixels``
    reads from it while it is bound, so nothing else about a caller's drawing
    has to change.

    Its colour is at ``GL_COLOR_ATTACHMENT0`` rather than ``GL_BACK_LEFT``,
    which is what a caller asking the framebuffer about its own buffers has to
    name.
    """

    def __init__(self, width, height, color_format=None):
        from OpenGL import GL as gl

        if color_format is None:
            color_format = gl.GL_RGBA8
        self.color_format = color_format
        self.width, self.height = width, height
        self.framebuffer = int(gl.glGenFramebuffers(1))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer)
        self.color = int(gl.glGenRenderbuffers(1))
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.color)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, color_format, width, height)
        gl.glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
            gl.GL_RENDERBUFFER, self.color)
        self.depth = int(gl.glGenRenderbuffers(1))
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depth)
        gl.glRenderbufferStorage(
            gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, width, height)
        gl.glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT,
            gl.GL_RENDERBUFFER, self.depth)
        status = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
        if status != gl.GL_FRAMEBUFFER_COMPLETE:
            self.release()
            raise CGLError('glCheckFramebufferStatus -> %s' % (status,), 10011)
        gl.glViewport(0, 0, width, height)

    def release(self):
        from OpenGL import GL as gl

        for name, delete in (
            ('color', gl.glDeleteRenderbuffers),
            ('depth', gl.glDeleteRenderbuffers),
            ('framebuffer', gl.glDeleteFramebuffers),
        ):
            value = getattr(self, name, None)
            if value:
                delete(1, [value])
                setattr(self, name, None)
