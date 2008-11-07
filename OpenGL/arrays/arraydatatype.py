"""Array data-type implementations (abstraction points for GL array types"""
import ctypes
import OpenGL
from OpenGL import constants, plugins
from OpenGL.arrays import formathandler
from OpenGL import logs
log = logs.getLog( 'OpenGL.arrays.arraydatatype' )

class ArrayDatatype( object ):
	"""Mix-in for array datatype classes
	
	The ArrayDatatype marker essentially is used to mark a particular argument
	as having an "array" type, which means that it is eligible for handling 
	via the arrays sub-package and its registered handlers.
	"""
	typeConstant = None
	def getHandler( cls, value ):
		"""Retrieve a handler for the given value, raise error on lookup failure"""
		typ = value.__class__
		try:
			handler = cls.TYPE_REGISTRY.get( typ )
		except AttributeError, err:
			formathandler.FormatHandler.loadAll()
			cls.TYPE_REGISTRY = formathandler.FormatHandler.TYPE_REGISTRY
			handler = cls.TYPE_REGISTRY.get( typ )
			if handler is None: 
				handler = plugins.FormatHandler.match( typ )
		if handler is None:
			if hasattr( typ, '__mro__' ):
				for base in typ.__mro__:
					handler = cls.TYPE_REGISTRY.get( base )
					if handler is None:
						handler = plugins.FormatHandler.match( base )
					if handler:
						handler = cls.TYPE_REGISTRY[ base ]
						handler.registerEquivalent( typ, base )
						cls.TYPE_REGISTRY[ typ ] = handler 
						return handler
			raise TypeError(
				"""No array-type handler for type %r (value: %s) registered"""%(
					typ, repr(value)[:50]
				)
			)
		return handler
	getHandler = classmethod( getHandler )
	def from_param( cls, value ):
		"""Given a value in a known data-pointer type, convert to a ctypes pointer"""
		return cls.getHandler(value).from_param( value )
	from_param = classmethod( logs.logOnFail( from_param, log ) )
	def dataPointer( cls, value ):
		"""Given a value in a known data-pointer type, return long for pointer"""
		try:
			return cls.getHandler(value).dataPointer( value )
		except Exception, err:
			log.warn(
				"""Failure in from_param for %s instance %s""", type(value), value,
			)
			raise
	dataPointer = classmethod( logs.logOnFail( dataPointer, log ) )
	def voidDataPointer( cls, value ):
		"""Given value in a known data-pointer type, return void_p for pointer"""
		return ctypes.c_void_p( cls.dataPointer( value ))
	voidDataPointer = classmethod( logs.logOnFail( voidDataPointer, log ) )
	def typedPointer( cls, value ):
		"""Return a pointer-to-base-type pointer for given value"""
		return ctypes.cast( cls.dataPointer(value), ctypes.POINTER( cls.baseType ))
	typedPointer = classmethod( typedPointer )
	def asArray( cls, value, typeCode=None ):
		"""Given a value, convert to preferred array representation"""
		return cls.getHandler(value).asArray( value, typeCode or cls.typeConstant )
	asArray = classmethod( logs.logOnFail( asArray, log ) )
	def arrayToGLType( cls, value ):
		"""Given a data-value, guess the OpenGL type of the corresponding pointer"""
		return cls.getHandler(value).arrayToGLType( value )
	arrayToGLType = classmethod( logs.logOnFail( arrayToGLType, log ) )
	def arraySize( cls, value, typeCode = None ):
		"""Given a data-value, calculate dimensions for the array (number-of-units)"""
		return cls.getHandler(value).arraySize( value, typeCode or cls.typeConstant )
	arraySize = classmethod( logs.logOnFail( arraySize, log ) )
	def unitSize( cls, value, typeCode=None ):
		"""Determine unit size of an array (if possible)
		
		Uses our local type if defined, otherwise asks the handler to guess...
		"""
		return cls.getHandler(value).unitSize( value, typeCode or cls.typeConstant )
	unitSize = classmethod( logs.logOnFail( unitSize, log ) )
	def returnHandler( cls ):
		"""Get the default return-handler"""
		try:
			return formathandler.FormatHandler.RETURN_HANDLER
		except AttributeError, err:
			if not formathandler.FormatHandler.TYPE_REGISTRY:
				formathandler.FormatHandler.loadAll()
			return formathandler.FormatHandler.chooseOutput( )
	returnHandler = classmethod( logs.logOnFail( returnHandler, log ) )
	def zeros( cls, dims, typeCode=None ):
		"""Allocate a return array of the given dimensions filled with zeros"""
		return cls.returnHandler().zeros( dims, typeCode or cls.typeConstant )
	zeros = classmethod( logs.logOnFail( zeros, log ) )
	def dimensions( cls, value ):
		"""Given a data-value, get the dimensions (assumes full structure info)"""
		return cls.getHandler(value).dimensions( value )
	dimensions = classmethod( logs.logOnFail( dimensions, log ) )
	
	def arrayByteCount( cls, value ):
		"""Given a data-value, try to determine number of bytes it's final form occupies
		
		For most data-types this is arraySize() * atomic-unit-size
		"""
		return cls.getHandler(value).arrayByteCount( value )
	arrayByteCount = classmethod( logs.logOnFail( arrayByteCount, log ) )
		

# the final array data-type classes...
class GLclampdArray( ArrayDatatype, ctypes.POINTER(constants.GLclampd )):
	"""Array datatype for GLclampd types"""
	baseType = constants.GLclampd
	typeConstant = constants.GL_DOUBLE

class GLclampfArray( ArrayDatatype, ctypes.POINTER(constants.GLclampf )):
	"""Array datatype for GLclampf types"""
	baseType = constants.GLclampf
	typeConstant = constants.GL_FLOAT

class GLfloatArray( ArrayDatatype, ctypes.POINTER(constants.GLfloat )):
	"""Array datatype for GLfloat types"""
	baseType = constants.GLfloat
	typeConstant = constants.GL_FLOAT

class GLdoubleArray( ArrayDatatype, ctypes.POINTER(constants.GLdouble )):
	"""Array datatype for GLdouble types"""
	baseType = constants.GLdouble
	typeConstant = constants.GL_DOUBLE

class GLbyteArray( ArrayDatatype, ctypes.POINTER(constants.GLbyte )):
	"""Array datatype for GLbyte types"""
	baseType = constants.GLbyte
	typeConstant = constants.GL_BYTE

class GLcharArray( ArrayDatatype, ctypes.c_char_p):
	"""Array datatype for ARB extension pointers-to-arrays"""
	baseType = constants.GLchar
	typeConstant = constants.GL_BYTE
GLcharARBArray = GLcharArray

class GLshortArray( ArrayDatatype, ctypes.POINTER(constants.GLshort )):
	"""Array datatype for GLshort types"""
	baseType = constants.GLshort
	typeConstant = constants.GL_SHORT

class GLintArray( ArrayDatatype, ctypes.POINTER(constants.GLint )):
	"""Array datatype for GLint types"""
	baseType = constants.GLint
	typeConstant = constants.GL_INT

class GLubyteArray( ArrayDatatype, ctypes.POINTER(constants.GLubyte )):
	"""Array datatype for GLubyte types"""
	baseType = constants.GLubyte
	typeConstant = constants.GL_UNSIGNED_BYTE
GLbooleanArray = GLubyteArray

class GLushortArray( ArrayDatatype, ctypes.POINTER(constants.GLushort )):
	"""Array datatype for GLushort types"""
	baseType = constants.GLushort
	typeConstant = constants.GL_UNSIGNED_SHORT

class GLuintArray( ArrayDatatype, ctypes.POINTER(constants.GLuint )):
	"""Array datatype for GLuint types"""
	baseType = constants.GLuint
	typeConstant = constants.GL_UNSIGNED_INT

class GLenumArray( ArrayDatatype, ctypes.POINTER(constants.GLenum )):
	"""Array datatype for GLenum types"""
	baseType = constants.GLenum
	typeConstant = constants.GL_UNSIGNED_INT
class GLsizeiArray( ArrayDatatype, ctypes.POINTER(constants.GLsizei )):
	"""Array datatype for GLenum types"""
	baseType = constants.GLsizei
	typeConstant = constants.GL_INT

GL_CONSTANT_TO_ARRAY_TYPE = {
	constants.GL_DOUBLE : GLclampdArray,
	constants.GL_FLOAT : GLclampfArray,
	constants.GL_FLOAT : GLfloatArray,
	constants.GL_DOUBLE : GLdoubleArray,
	constants.GL_BYTE : GLbyteArray,
	constants.GL_SHORT : GLshortArray,
	constants.GL_INT : GLintArray,
	constants.GL_UNSIGNED_BYTE : GLubyteArray,
	constants.GL_UNSIGNED_SHORT : GLushortArray,
	constants.GL_UNSIGNED_INT : GLuintArray,
	#constants.GL_UNSIGNED_INT : GLenumArray,
}
