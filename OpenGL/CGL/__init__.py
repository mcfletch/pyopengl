"""CGL, the macOS interface that creates OpenGL contexts without a window.

CGL (Core OpenGL) is the lowest-level OpenGL interface on macOS.  NSGL, the
OpenGL interface in Apple's AppKit framework (`NSOpenGLContext
<https://developer.apple.com/documentation/appkit/nsopenglcontext>`__ and
``NSOpenGLPixelFormat``), is built on it.  GUI toolkits use NSGL to create an
OpenGL context for a window.  CGL can create a context with no window and no
window server, for offscreen rendering::

    from OpenGL.CGL import headless_context

    with headless_context() as context:
        ...                                 # the context is current here

PyOpenGL's test suite uses this module for its offscreen contexts on macOS
(``TEST_WINDOWING=cgl``).  :mod:`OpenGL.Tk` on Aqua creates its context with
NSGL, and uses this module to choose the pixel format and profile.

An offscreen context created with CGL does not have a default framebuffer, so
rendering must target a framebuffer object.  :func:`headless_context` creates
only the context; :class:`OffscreenTarget` is a framebuffer object with colour,
depth and stencil attachments to bind to it.

A machine with no accelerated renderer, such as a virtual machine or a session
with no window server, has only Apple's software renderer, and a pixel format
that requires acceleration fails there.  :func:`pixel_format_attributes` builds
the attribute list for an accelerated renderer, for any renderer, or for the
software renderer.  :func:`choose_pixel_format` tries those three in that
order and reports which one it used.

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

#: The profiles CGL offers, keyed by the names this module uses.  macOS has
#: no compatibility profile above 2.1.  ``'legacy'`` is GL 2.1 with the
#: fixed-function pipeline.  The two core profiles have no fixed-function
#: pipeline.
PROFILES = {
    'legacy': kCGLOGLPVersion_Legacy,
    'core3': kCGLOGLPVersion_3_2_Core,
    'core4': kCGLOGLPVersion_GL4_Core,
}

#: The GL version each profile promises.  Compare it with the version the
#: context reports.  CGL accepts a pixel format naming a profile the renderer
#: cannot provide, and returns a context with a lower version.  macOS resolves
#: every entry point from the framework, whether or not the current context
#: implements it, so calling a function the context lacks segfaults.
PROFILE_VERSIONS = {
    'legacy': (2, 1),
    'core3': (3, 2),
    'core4': (4, 1),
}

#: The highest GL version macOS provides, from the 4.1 core profile.  macOS
#: has no GL 4.2.
MAX_VERSION = (4, 1)

#: The lowest GL version each CGL profile provides, highest first.  macOS
#: serves a request for 3.2 or above with a core profile, and has no
#: compatibility profile at those versions.  The legacy profile is GL 2.1 and
#: is the only one with the fixed-function pipeline.
_PROFILE_FLOORS = (
    ((4, 1), 'core4'),
    ((3, 2), 'core3'),
    ((0, 0), 'legacy'),
)

_ES_APIS = ('gles', 'es')


def profile_for(api, profile, gl_version):
    """The CGL profile for a context request, or ``None`` and a reason.

    Returns ``(profile_name, None)`` or ``(None, reason)``, where
    ``profile_name`` is a key of :data:`PROFILES`.  ``api`` is ``'gl'`` or
    ``'gles'``, ``profile`` is ``'core'`` or ``'compatibility'`` and
    ``gl_version`` is a ``(major, minor)`` pair.  The function makes no CGL
    calls, so it runs on any platform.  It refuses OpenGL-ES, which CGL does
    not provide, and a compatibility profile above 2.1, which macOS does not
    have.  It also refuses a core profile below 3.2.
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


#: The leading ``major.minor`` of a ``GL_VERSION`` string, after any API name.
#: Desktop GL starts with the number.  OpenGL-ES puts "OpenGL ES" (or
#: "OpenGL ES-CM") in front of it.
_VERSION = re.compile(r'(?:OpenGL\s+ES(?:-CM|-SC)?\s+)?(\d+)\.(\d+)')


def parse_gl_version(reported):
    """``(major, minor)`` from a ``GL_VERSION`` string, or ``None``.

    Only the leading number is read.  The text after it is a vendor-specific
    driver description.
    """
    if not reported:
        return None
    found = _VERSION.match(reported.strip())
    if not found:
        return None
    return (int(found.group(1)), int(found.group(2)))


def version_shortfall(reported, wanted):
    """A message saying why ``reported`` is below ``wanted``, or ``None``.

    A context can have a lower version than the one requested.  GLFW fails to
    create a window when the driver cannot meet the request.  CGL accepts a
    pixel format naming the 3.2 core profile on a renderer that implements
    2.1, and returns a 2.1 context.

    macOS exports every entry point from the framework, whether or not the
    current context implements it.  A GL 3.1 call on a 2.1 context therefore
    resolves, runs and segfaults the process.

    Returns ``None`` when ``reported`` cannot be parsed, so an unrecognised
    driver string does not cause every test using the context to be skipped.
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

#: The renderer kinds :func:`pixel_format_attributes` accepts.  ``'any'``
#: states no preference.  Use it on a machine with no accelerated renderer,
#: where a request for acceleration fails and does not fall back.
RENDERER_KINDS = ('accelerated', 'any', 'software')

# -- renderer properties (CGLTypes.h) --------------------------------------
#
# CGLQueryRendererInfo describes this machine's renderers without creating a
# context.  It is the only way to learn what a context would support before
# creating one.

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
    """The properties of one renderer on this machine.

    ``major_gl_version`` is the highest GL major version the renderer
    supports.  A context gets the requested core profile only if this is high
    enough.  CGL accepts a pixel format naming a profile the renderer cannot
    provide, and returns a context with a lower version.
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

    Creates no context and opens no window, so it works on a machine where
    context creation fails.  Use it to find out why a context does not have
    the requested version or renderer.
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
    """A CGL call returned an error.

    ``code`` is the ``CGLError`` value and ``operation`` is the call that
    returned it.  A caller can use ``code`` to tell a missing pixel format
    from bad arguments without parsing the message.
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

    The library is loaded on first use.  The module can be imported on a
    platform without CGL, and its attribute-building functions can be used and
    tested there.
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

    The function makes no CGL calls, so it runs on any platform.  ``profile``
    is a key of :data:`PROFILES` and ``renderer`` is one of
    :data:`RENDERER_KINDS`.  The sizes are bits per buffer.  As in CGL,
    ``color_size`` counts the three colour channels together.  ``stereo``
    requests a stereo pair of colour buffers, which few renderers offer.

    The list ends with a zero, as CGL requires.
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
        # CGL has no "not accelerated" attribute.  Naming the renderer id is
        # the only way to request the CPU renderer.
        attributes += [kCGLPFARendererID, kCGLRendererGenericFloatID]
    # 'any' adds neither attribute, and CGL picks any available renderer.
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


#: The renderer kinds tried in order when none is named.  'accelerated' is
#: first, to use a GPU if there is one.  'any' covers a machine whose only
#: renderer is Apple's CPU renderer under an id other than the generic-float
#: id.  'software', which names the generic-float id, is last.
RENDERER_ORDER = ('accelerated', 'any', 'software')


def pixel_format_candidates(profile='legacy', renderer=None, **sizes):
    """The pixel formats to try, as ``(renderer_kind, attribute_array)`` pairs.

    With ``renderer`` given, only that kind is yielded.  Otherwise the kinds
    in :data:`RENDERER_ORDER` are yielded in order, and the caller takes the
    first one the machine accepts.  Each array is a ctypes array of
    ``CGLPixelFormatAttribute`` ending in zero, the form both
    ``CGLChoosePixelFormat`` and ``NSOpenGLPixelFormat`` take.  ``sizes`` are
    the size arguments of :func:`pixel_format_attributes`.
    """
    kinds = (renderer,) if renderer is not None else RENDERER_ORDER
    for kind in kinds:
        attributes = pixel_format_attributes(
            profile=profile, renderer=kind, **sizes)
        yield kind, (CGLPixelFormatAttribute * len(attributes))(*attributes)


def choose_pixel_format(profile='legacy', renderer=None, **sizes):
    """A pixel format for this machine, and the renderer kind it came from.

    Returns ``(pixel_format, renderer_kind)`` for the first of
    :func:`pixel_format_candidates` the machine accepts.  A Mac with a GPU
    gets an accelerated pixel format.  A virtual machine or a session with no
    window server gets the software renderer.

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
    """Set the number of display refreshes between buffer swaps.

    ``context`` is a ``CGLContextObj``.  An ``interval`` of zero swaps without
    waiting for the display, for benchmarks.  Returns True if the parameter was
    set, and False if the renderer rejected it.
    """
    value = GLint(int(interval))
    return library().CGLSetParameter(
        context, kCGLCPSwapInterval, ctypes.byref(value)) == 0


# -- a context ---------------------------------------------------------------

@contextlib.contextmanager
def headless_context(profile='legacy', renderer=None, **sizes):
    """A CGL context with no drawable, current for the body and then destroyed.

    Yields the ``CGLContextObj``.  ``profile`` is a key of :data:`PROFILES`,
    and the remaining arguments are those of :func:`pixel_format_attributes`.
    The context has no default framebuffer, so bind an :class:`OffscreenTarget`
    before drawing.
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
    """A framebuffer object for a context that has no default framebuffer.

    Create it while a context is current.  The constructor binds it, and
    :meth:`release` deletes it.  ``color_format`` is the internal format of
    the colour attachment, ``GL_RGBA8`` by default.  Pass ``GL_RGB8`` for
    readback without alpha.  The depth/stencil attachment is
    ``GL_DEPTH24_STENCIL8``.  ``glReadPixels`` reads from the target while it
    is bound.

    The colour buffer is ``GL_COLOR_ATTACHMENT0``.  Queries about the
    framebuffer's buffers must name that attachment, and not ``GL_BACK_LEFT``.
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
