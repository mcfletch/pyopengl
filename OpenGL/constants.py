"""OpenGL-wide constant types (not OpenGL.GL-specific"""
import ctypes
from OpenGL.constant import Constant

GL_FALSE = Constant( 'GL_FALSE', 0x0 )
GL_TRUE = Constant( 'GL_TRUE', 0x1 )
GL_BYTE = Constant( 'GL_BYTE', 0x1400 )
GL_UNSIGNED_BYTE = Constant( 'GL_UNSIGNED_BYTE', 0x1401 )
GL_SHORT = Constant( 'GL_SHORT', 0x1402 )
GL_UNSIGNED_SHORT = Constant( 'GL_UNSIGNED_SHORT', 0x1403 )
GL_INT = Constant( 'GL_INT', 0x1404 )
GL_UNSIGNED_INT = Constant( 'GL_UNSIGNED_INT', 0x1405 )
GL_FLOAT = Constant( 'GL_FLOAT', 0x1406 )
GL_DOUBLE = Constant( 'GL_DOUBLE', 0x140a )
GL_CHAR = str
GL_HALF_NV = Constant( 'GL_HALF_NV', 0x1401 )

# Basic OpenGL data-types as ctypes declarations...
def _defineType( name, baseType, convertFunc = long ):
	import OpenGL 
	if OpenGL.ALLOW_NUMPY_SCALARS:
		original = baseType.from_param
		def from_param( x ):
			try:
				return original( x )
			except TypeError, err:
				try:
					return original( convertFunc(x) )
				except TypeError, err2:
					raise err
		setattr( baseType, 'from_param', staticmethod( from_param ) )
		return baseType
	else:
		return baseType

GLvoid = None
GLboolean = _defineType( 'GLboolean', ctypes.c_ubyte, bool )
GLenum = _defineType( 'GLenum', ctypes.c_uint )

GLfloat = _defineType( 'GLfloat', ctypes.c_float, float )
GLdouble = _defineType( 'GLdouble', ctypes.c_double, float )

GLbyte = ctypes.c_byte
GLshort = _defineType( 'GLshort', ctypes.c_short, int )
GLint = _defineType( 'GLint', ctypes.c_int, int )
GLuint = _defineType( 'GLuint', ctypes.c_uint )

GLsizei = _defineType( 'GLsizei', ctypes.c_int, int )

GLubyte = ctypes.c_ubyte
GLushort = _defineType( 'GLushort', ctypes.c_ushort, int )
GLhandleARB = _defineType( 'GLhandleARB', ctypes.c_uint )
GLhandle = _defineType( 'GLhandle', ctypes.c_uint )

GLchar = GLcharARB = ctypes.c_char

GLbitfield = _defineType( 'GLbitfield', ctypes.c_uint )

GLclampd = _defineType( 'GLclampd', ctypes.c_double, float )
GLclampf = _defineType( 'GLclampf', ctypes.c_float, float )

# ptrdiff_t, actually...
GLsizeiptrARB = GLsizeiptr = GLsizei
GLintptrARB = GLintptr = GLint
size_t = ctypes.c_ulong

GLhalfNV = GLhalfARB = ctypes.c_ushort


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
