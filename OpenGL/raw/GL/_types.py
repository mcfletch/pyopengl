# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL-wide constant types (not OpenGL.GL-specific)

These are basically the fundamental data-types that OpenGL 
uses (note, doesn't include the OpenGL-ES types!)
"""
import ctypes
from OpenGL.constant import Constant
from OpenGL._bytes import bytes,unicode,as_8_bit, long
assert unicode
assert as_8_bit
from OpenGL._opaque import opaque_pointer_cls as _opaque_pointer_cls

sizeof = ctypes.sizeof
# `int`, because that is what each of these *is*: `Constant` answers an
# `IntConstant` for an integer value.  The generated stubs declare the same
# names `int`, and every generated extension stub star-imports this module
# alongside them -- so a checker compares the two declarations in any program
# that imports GL and an extension, and two answers there is an error in that
# program rather than a difference of description.
GL_FALSE: int = Constant( 'GL_FALSE', 0x0 )
GL_TRUE: int = Constant( 'GL_TRUE', 0x1 )
GL_BYTE: int = Constant( 'GL_BYTE', 0x1400 )
GL_UNSIGNED_BYTE: int = Constant( 'GL_UNSIGNED_BYTE', 0x1401 )
GL_SHORT: int = Constant( 'GL_SHORT', 0x1402 )
GL_UNSIGNED_SHORT: int = Constant( 'GL_UNSIGNED_SHORT', 0x1403 )
GL_INT: int = Constant( 'GL_INT', 0x1404 )
GL_UNSIGNED_INT: int = Constant( 'GL_UNSIGNED_INT', 0x1405 )
GL_UNSIGNED_INT64: int = Constant( 'GL_UNSIGNED_INT64_AMD', 0x8BC2 )
GL_INT64: int = Constant( 'GL_INT64_NV', 0x140E )
GL_FLOAT: int = Constant( 'GL_FLOAT', 0x1406 )
GL_DOUBLE: int = Constant( 'GL_DOUBLE', 0x140a )
GL_CHAR = bytes
GL_HALF_FLOAT: int = Constant( 'GL_HALF_FLOAT_ARB',0x140B)
GL_HALF_NV: int = Constant( 'GL_HALF_NV', 0x1401 )
GL_FIXED: int = Constant('GL_FIXED',0x140C)
GL_VOID_P = object()

def _get_ctypes_version():
    return [int(i) for i in ctypes.__version__.split('.')[:3]]
ctypes_version = _get_ctypes_version()


# Basic OpenGL data-types as ctypes declarations...
def _defineType(name, baseType, convertFunc=long):
    """Name a GL scalar type after the ctypes type that carries it.

    ``convertFunc`` is kept in the signature because the generated modules and
    OpenGL.raw.GLES1 pass it positionally; nothing reads it.  It named the
    conversion ``ALLOW_NUMPY_SCALARS`` used to retry through, which is gone --
    see that flag in ``OpenGL/__init__.py``.
    """
    return baseType

GLvoid = None
GLboolean = _defineType( 'GLboolean', ctypes.c_ubyte, bool )
GLenum = _defineType( 'GLenum', ctypes.c_uint )

GLfloat = _defineType( 'GLfloat', ctypes.c_float, float )
GLfloat_2 = GLfloat * 2
GLfloat_3 = GLfloat * 3
GLfloat_4 = GLfloat * 4
GLdouble = _defineType( 'GLdouble', ctypes.c_double, float )
GLdouble_2 = GLdouble * 2
GLdouble_3 = GLdouble * 3
GLdouble_4 = GLdouble * 4

GLbyte = ctypes.c_byte
GLshort = _defineType( 'GLshort', ctypes.c_short, int )
GLint = _defineType( 'GLint', ctypes.c_int, int )
GLuint = _defineType( 'GLuint', ctypes.c_uint, long )
GLfixed = _defineType('GLfixed', ctypes.c_int32, int )
GLclampx = _defineType('GLclampx', ctypes.c_int32, int )

# This is explicitly called out as equivalent to a uint
GLsizei = _defineType( 'GLsizei', ctypes.c_uint, long )
# Signed 2's complement binary integer with sizeof( void * )
GLintptr = _defineType( 'GLintptr', ctypes.c_ssize_t, int )
# Unsigned size-of-x.  Khronos declares this signed -- glcorearb.h has
# `typedef khronos_ssize_t GLsizeiptr` -- and GLintptr above follows that while
# this does not.  A size or a length arrives non-negative, so the two agree on
# every value the API produces, and everything built on this one is unsigned to
# match: the numpy dtype, the buffer format the C element table accepts, and
# GLsizeiptrArray.  Changing the type alone would leave those disagreeing with
# it, so change them together or not at all.
GLsizeiptr = _defineType( 'GLsizeiptr', ctypes.c_size_t, int )

GLubyte = ctypes.c_ubyte
GLubyte_3 = GLubyte * 3
GLushort = _defineType( 'GLushort', ctypes.c_ushort, int )
GLulong = _defineType( 'GLulong', ctypes.c_ulong, int )
GLhandleARB = _defineType( 'GLhandleARB', ctypes.c_uint, long )
GLhandle = _defineType( 'GLhandle', ctypes.c_uint, long )

GLchar = GLcharARB = ctypes.c_char

GLbitfield = _defineType( 'GLbitfield', ctypes.c_uint, long )

GLclampd = _defineType( 'GLclampd', ctypes.c_double, float )
GLclampf = _defineType( 'GLclampf', ctypes.c_float, float )

GLuint64 = GLuint64EXT = _defineType('GLuint64', ctypes.c_uint64, long )
GLint64 = GLint64EXT = _defineType('GLint64', ctypes.c_int64, long )

# ptrdiff_t, actually...
GLsizeiptrARB = GLsizeiptr
GLvdpauSurfaceNV = GLintptrARB = GLintptr
size_t = ctypes.c_size_t
int32_t = ctypes.c_int32
int64_t = ctypes.c_int64

void = None

# this is *wrong*, half is a *float* type, but ctypes doesn't have 16-bit float support
GLhalfNV = GLhalfARB = ctypes.c_ushort

# GL.ARB.sync extension, GLsync is an opaque pointer to a struct 
# in the extensions header, basically just a "token" that can be 
# passed to the various operations...
GLsync = _opaque_pointer_cls( 'GLsync' )
GLvoidp = ctypes.c_void_p

ARRAY_TYPE_TO_CONSTANT = [
    ('GLclampd', GL_DOUBLE),
    ('GLclampf', GL_FLOAT),
    ('GLfloat', GL_FLOAT),
    ('GLdouble', GL_DOUBLE),
    ('GLbyte', GL_BYTE),
    ('GLshort', GL_SHORT),
    ('GLint', GL_INT),
    ('GLubyte', GL_UNSIGNED_BYTE),
    ('GLushort', GL_UNSIGNED_SHORT),
    ('GLuint', GL_UNSIGNED_INT),
    ('GLenum', GL_UNSIGNED_INT),
]

from OpenGL.platform import PLATFORM as _p

GLDEBUGPROCARB = GLDEBUGPROCKHR = GLDEBUGPROC = _p.DEFAULT_FUNCTION_TYPE(
    void, 
    GLenum,  # source,
    GLenum, #type,
    GLuint, # id 
    GLenum, # severity
    GLsizei, # length
    ctypes.c_char_p, # message 
    GLvoidp, # userParam
)

class _cl_context( ctypes.Structure ):
    """Placeholder/empty structure for _cl_context"""
class _cl_event( ctypes.Structure ):
    """Placeholder/empty structure for _cl_event"""
    
GLDEBUGPROCAMD = _p.DEFAULT_FUNCTION_TYPE(
    void,
    GLuint,# id,
    GLenum,# category,
    GLenum,# severity,
    GLsizei,# length,
    ctypes.c_char_p,# message,
    GLvoidp,# userParam
)

GLeglImageOES = GLvoidp 
c_int = ctypes.c_int

