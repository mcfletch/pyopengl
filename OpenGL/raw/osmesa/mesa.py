# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL import arrays
from OpenGL.raw.GL._types import GLenum,GLboolean,GLsizei,GLint,GLuint
from OpenGL.raw.osmesa._types import *
from OpenGL.constant import Constant as _C
from OpenGL import platform as _p
import ctypes

def _f( function ):
    return _p.createFunction( 
        function,_p.PLATFORM.OSMesa,
        None,
        error_checker=None
    )

OSMESA_COLOR_INDEX = _C('OSMESA_COLOR_INDEX', 6400)
OSMESA_RGBA = _C('OSMESA_RGBA', 6408)
OSMESA_BGRA = _C('OSMESA_BGRA', 0x1)
OSMESA_ARGB = _C('OSMESA_ARGB', 0x2)
OSMESA_RGB = _C('OSMESA_RGB', 6407)
OSMESA_BGR = _C('OSMESA_BGR',	0x4)
OSMESA_RGB_565 = _C('OSMESA_RGB_565', 0x5)
OSMESA_ROW_LENGTH = _C('OSMESA_ROW_LENGTH', 0x10)
OSMESA_Y_UP = _C('OSMESA_Y_UP', 0x11)
OSMESA_WIDTH = _C('OSMESA_WIDTH', 0x20)
OSMESA_HEIGHT = _C('OSMESA_HEIGHT', 0x21)
OSMESA_FORMAT = _C('OSMESA_FORMAT', 0x22)
OSMESA_TYPE = _C('OSMESA_TYPE', 0x23)
OSMESA_MAX_WIDTH = _C('OSMESA_MAX_WIDTH', 0x24)
OSMESA_MAX_HEIGHT = _C('OSMESA_MAX_HEIGHT', 0x25)
OSMESA_DEPTH_BITS = _C('OSMESA_DEPTH_BITS', 0x30)
OSMESA_STENCIL_BITS = _C('OSMESA_STENCIL_BITS', 0x31)
OSMESA_ACCUM_BITS = _C('OSMESA_ACCUM_BITS', 0x32)
OSMESA_PROFILE = _C('OSMESA_PROFILE', 0x33)
OSMESA_CORE_PROFILE = _C('OSMESA_CORE_PROFILE', 0x34)
OSMESA_COMPAT_PROFILE = _C('OSMESA_COMPAT_PROFILE', 0x35)
OSMESA_CONTEXT_MAJOR_VERSION = _C('OSMESA_CONTEXT_MAJOR_VERSION', 0x36)
OSMESA_CONTEXT_MINOR_VERSION = _C('OSMESA_CONTEXT_MINOR_VERSION', 0x37)

OSMesaGetCurrentContext = _p.GetCurrentContext

@_f
@_p.types(OSMesaContext,GLenum, OSMesaContext)
def OSMesaCreateContext(format,sharelist): pass

@_f
@_p.types(OSMesaContext,GLenum, GLint, GLint, GLint, OSMesaContext)
def OSMesaCreateContextExt(format, depthBits, stencilBits,accumBits,sharelist ): pass

@_f
@_p.types(OSMesaContext,arrays.GLintArray, OSMesaContext)
def OSMesaCreateContextAttribs(attribList,sharelist ): pass

@_f
@_p.types(None, OSMesaContext)
def OSMesaDestroyContext(ctx): pass

@_f 
@_p.types(GLboolean, OSMesaContext, ctypes.POINTER(None), GLenum, GLsizei, GLsizei )
def OSMesaMakeCurrent( ctx, buffer, type,width,height ): pass

@_f
# void OSMesaPixelStore( GLint pname, GLint value )
#
# The names matter as much as the types: they are the signature a caller
# reads, and what a keyword call binds to.  These said
# `(ctx, buffer, type, width, height)`, copied from OSMesaMakeCurrent above,
# so the two-argument call the declared types describe could only be made
# positionally.
@_p.types(None, GLint, GLint)
def OSMesaPixelStore( pname, value ): pass

# The three entry points that answer through pointer arguments.  The name each
# one has is the Python function below it, which allocates those arguments and
# reads them back, so the declaration is held privately here.
#
# Declared, rather than reached for as `_p.PLATFORM.GL.<name>`: an undeclared
# ctypes call reads a result as a C `int`, and the two queries answer with a
# GLboolean, which is one byte.  The three bytes above it are whatever the call
# left in the register, so an undeclared "no" reads as a no or as a yes
# according to the ABI -- and read as a yes it hands the caller the width, the
# height and the buffer pointer that the call never wrote.
def _query( name, resultType, argTypes, argNames, doc ):
    """An OSMesa entry point with the types its C declaration gives it"""
    return _p.createBaseFunction(
        name, dll=_p.PLATFORM.OSMesa, resultType=resultType,
        argTypes=argTypes, argNames=argNames, doc=doc,
    )

_OSMesaGetIntegerv = _query(
    'OSMesaGetIntegerv', None,
    [GLint, ctypes.POINTER(GLint)],
    ('pname', 'value'),
    'OSMesaGetIntegerv( GLint(pname), POINTER(GLint)(value) ) -> None',
)
_OSMesaGetDepthBuffer = _query(
    'OSMesaGetDepthBuffer', GLboolean,
    [OSMesaContext, ctypes.POINTER(GLint), ctypes.POINTER(GLint),
     ctypes.POINTER(GLint), ctypes.POINTER(ctypes.POINTER(GLint))],
    ('c', 'width', 'height', 'bytesPerValue', 'buffer'),
    'OSMesaGetDepthBuffer( OSMesaContext(c), POINTER(GLint)(width), '
    'POINTER(GLint)(height), POINTER(GLint)(bytesPerValue), '
    'POINTER(POINTER(GLint))(buffer) ) -> GLboolean',
)
_OSMesaGetColorBuffer = _query(
    'OSMesaGetColorBuffer', GLboolean,
    [OSMesaContext, ctypes.POINTER(GLint), ctypes.POINTER(GLint),
     ctypes.POINTER(GLint), ctypes.POINTER(ctypes.c_void_p)],
    ('c', 'width', 'height', 'format', 'buffer'),
    'OSMesaGetColorBuffer( OSMesaContext(c), POINTER(GLint)(width), '
    'POINTER(GLint)(height), POINTER(GLint)(format), '
    'POINTER(c_void_p)(buffer) ) -> GLboolean',
)

def OSMesaGetIntegerv(pname):
    """The value OSMesa holds for `pname`, such as OSMESA_WIDTH"""
    value = GLint()
    _OSMesaGetIntegerv(pname, ctypes.byref(value))
    return value.value

def OSMesaGetDepthBuffer(c):
    """The depth buffer of context `c` as (width, height, bytesPerValue, pointer)

    ``(0, 0, 0, None)`` where there is none -- a context made with no depth
    bits, or one that has not been made current -- so the absence is read from
    the pointer rather than from an exception.
    """
    width, height, bytesPerValue = GLint(), GLint(), GLint()
    buffer = ctypes.POINTER(GLint)()

    if _OSMesaGetDepthBuffer(c, ctypes.byref(width),
                             ctypes.byref(height),
                             ctypes.byref(bytesPerValue),
                             ctypes.byref(buffer)) and buffer:
        return width.value, height.value, bytesPerValue.value, buffer
    else:
        return 0, 0, 0, None

def OSMesaGetColorBuffer(c):
    """The colour buffer of context `c` as (width, height, format, pointer)

    ``(0, 0, 0, None)`` where there is none: the buffer belongs to the
    make-current, so a context that has not had one is such a case.
    """
    # TODO: make output array types which can handle the operation
    # provide an API to convert pointers + sizes to array instances,
    # e.g. numpy.ctypeslib.as_array( ptr, bytesize ).astype( 'B' ).reshape( height,width )
    width, height, format = GLint(), GLint(), GLint()
    buffer = ctypes.c_void_p()

    if _OSMesaGetColorBuffer(c, ctypes.byref(width),
                             ctypes.byref(height),
                             ctypes.byref(format),
                             ctypes.byref(buffer)) and buffer:
        return width.value, height.value, format.value, buffer
    else:
        return 0, 0, 0, None

@_f
# void OSMesaColorClamp( GLboolean enable )
#
# `types(GLboolean)` named a GLboolean *return* and no arguments at all, which
# ctypes reads as "accepts anything": the call happened to work, and nothing
# checked the argument it was given.
@_p.types(None, GLboolean)
def OSMesaColorClamp(enable):
    """Enable/disable color clamping, off by default

    New in Mesa 6.4.2
    """

@_f
# void OSMesaPostprocess( OSMesaContext osmesa, const char *filter,
#                         GLuint enable_value )
#
# The context was missing from the types, so the first argument was read as
# the filter and the filter as the enable value: every call raised
# `ctypes.ArgumentError: argument 2` naming a position the signature does not
# have.
@_p.types(None, OSMesaContext, arrays.GLcharArray, GLuint)
def OSMesaPostprocess(osmesa, filter, enable_value):
    """Enable/disable Gallium post-process filters.

    This should be called after a context is created, but before it is
    made current for the first time.  After a context has been made
    current, this function has no effect.

    If the enable_value param is zero, the filter is disabled.  Otherwise
    the filter is enabled, and the value may control the filter's quality.
    New in Mesa 10.0
    """


__all__ = [
    'OSMesaCreateContext',
    'OSMesaCreateContextExt', 'OSMesaMakeCurrent', 'OSMesaGetIntegerv',
    'OSMesaGetCurrentContext', 'OSMesaDestroyContext', 'OSMesaPixelStore',
    'OSMesaGetDepthBuffer', 'OSMesaGetColorBuffer', 'OSMesaCreateContextAttribs',
    'OSMesaColorClamp','OSMesaPostprocess',
    'OSMESA_COLOR_INDEX', 'OSMESA_RGBA', 'OSMESA_BGRA', 'OSMESA_ARGB',
    'OSMESA_RGB', 'OSMESA_BGR', 'OSMESA_RGB_565', 'OSMESA_ROW_LENGTH',
    'OSMESA_Y_UP', 'OSMESA_WIDTH', 'OSMESA_HEIGHT', 'OSMESA_FORMAT',
    'OSMESA_TYPE', 'OSMESA_MAX_WIDTH', 'OSMESA_MAX_HEIGHT',
    'OSMESA_DEPTH_BITS', 'OSMESA_STENCIL_BITS', 'OSMESA_ACCUM_BITS',
    'OSMESA_PROFILE', 'OSMESA_CORE_PROFILE', 'OSMESA_COMPAT_PROFILE',
    'OSMESA_CONTEXT_MAJOR_VERSION', 'OSMESA_CONTEXT_MINOR_VERSION'
]
