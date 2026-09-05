"""CGL, the interface that gives macOS an OpenGL context with no window.

CGL is the layer NSGL and AGL are built on, and the only one of the three that
will hand out a context without a window server to put a window on.  That makes
it what an offscreen renderer, a batch tool or a CI job on macOS needs::

    from OpenGL.CGL import headless_context

    with headless_context() as context:
        ...                                 # the context is current here

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

__all__ = (
    'CGL_ERROR_NAMES',
    'PROFILES',
    'PROFILE_VERSIONS',
    'RENDERER_KINDS',
    'CGLError',
    'OffscreenTarget',
    'choose_pixel_format',
    'headless_context',
    'pixel_format_attributes',
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
        cgl.CGLDescribePixelFormat.argtypes = [
            CGLPixelFormatObj, GLint, CGLPixelFormatAttribute,
            ctypes.POINTER(GLint),
        ]
        cgl.CGLDescribePixelFormat.restype = ctypes.c_int32
        _cgl = cgl
    return _cgl


def _check(operation, code):
    if code != 0:
        raise CGLError(operation, code)
    return code


# -- choosing a pixel format -----------------------------------------------

def pixel_format_attributes(profile='legacy', renderer='accelerated',
                            color_size=24, alpha_size=8, depth_size=24,
                            stencil_size=8, samples=0, double_buffer=False):
    """The attribute list ``CGLChoosePixelFormat`` takes, as plain integers.

    Pure, so what a caller asked for can be read off without a Mac to ask.
    ``profile`` is a key of :data:`PROFILES` and ``renderer`` one of
    :data:`RENDERER_KINDS`; the sizes are bits per buffer, ``color_size``
    counting the three colour channels together as CGL does.

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


#: The renderer kinds :func:`choose_pixel_format` tries, in order.  A GPU is
#: worth having where there is one; 'any' is what answers on a machine whose
#: only renderer is Apple's CPU one but which does not advertise it under the
#: generic-float id; naming that id is the last resort.
_RENDERER_ORDER = ('accelerated', 'any', 'software')


def choose_pixel_format(profile='legacy', renderer=None, **sizes):
    """A pixel format for this machine, and the renderer kind it came from.

    Returns ``(pixel_format, renderer_kind)``.  With ``renderer`` given, that
    kind is the only one tried.  Without, the kinds in :data:`_RENDERER_ORDER`
    are tried in turn and the first the machine offers is taken -- so a Mac
    with a GPU renders on it, and a virtual machine or a session with no window
    server still gets a context instead of an error.

    Raises :class:`CGLError` if none of them is available.
    """
    cgl = library()
    kinds = (renderer,) if renderer is not None else _RENDERER_ORDER
    failure = None
    for kind in kinds:
        attributes = pixel_format_attributes(
            profile=profile, renderer=kind, **sizes)
        array = (CGLPixelFormatAttribute * len(attributes))(*attributes)
        pixel_format = CGLPixelFormatObj()
        count = GLint()
        code = cgl.CGLChoosePixelFormat(
            array, ctypes.byref(pixel_format), ctypes.byref(count))
        if code == 0 and pixel_format.value and count.value > 0:
            return pixel_format, kind
        failure = failure or CGLError('CGLChoosePixelFormat', code or 10002)
    raise failure


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
