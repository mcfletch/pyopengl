"""ctypes sized data-arrays as a data-formatmechanism

XXX we have to use _ctypes.Array as the type descriminator,
would be nice to have it available from the public module
"""
REGISTRY_NAME = 'ctypesarrays'
import ctypes, _ctypes

from OpenGL import constants, constant
from OpenGL.arrays import formathandler
import operator

class CtypesArrayHandler( formathandler.FormatHandler ):
    """Ctypes Array-type-specific data-type handler for OpenGL"""
    @classmethod
    def from_param( cls, value, typeCode=None ):
        return ctypes.byref( value )
    dataPointer = staticmethod( ctypes.addressof )
    HANDLED_TYPES = (_ctypes.Array, )
    isOutput = True
    def voidDataPointer( cls, value ):
        """Given value in a known data-pointer type, return void_p for pointer"""
        return ctypes.byref( value )
    def zeros( self, dims, typeCode ):
        """Return Numpy array of zeros in given size"""
        type = GL_TYPE_TO_ARRAY_MAPPING[ typeCode ]
        for dim in dims:
            type *= dim 
        return type() # should expicitly set to 0s
    def ones( self, dims, typeCode='d' ):
        """Return numpy array of ones in given size"""
        raise NotImplementedError( """Haven't got a good ones implementation yet""" )
##		type = GL_TYPE_TO_ARRAY_MAPPING[ typeCode ]
##		for dim in dims:
##			type *= dim 
##		return type() # should expicitly set to 0s
    def arrayToGLType( self, value ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        result = ARRAY_TO_GL_TYPE_MAPPING.get( value._type_ )
        if result is not None:
            return result
        raise TypeError(
            """Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
                value._type_, ARRAY_TO_GL_TYPE_MAPPING.keys(), value,
            )
        )
    def arraySize( self, value, typeCode = None ):
        """Given a data-value, calculate dimensions for the array"""
        try:
            return value.__class__.__component_count__
        except AttributeError, err:
            dims = 1
            for length in self.dims( value ):
                dims *= length
            value.__class__.__component_count__ = dims
            return dims 
    def arrayByteCount( self, value, typeCode = None ):
        """Given a data-value, calculate number of bytes required to represent"""
        return ctypes.sizeof( value )
    def types( self, value ):
        """Produce iterable producing all composite types"""
        dimObject = value
        while dimObject is not None:
            yield dimObject
            dimObject = getattr( dimObject, '_type_', None )
            if isinstance( dimObject, (str,unicode)):
                dimObject = None 
    def dims( self, value ):
        """Produce iterable of all dimensions"""
        try:
            return value.__class__.__dimensions__
        except AttributeError, err:
            dimensions = []
            for base in self.types( value ):
                length = getattr( base, '_length_', None)
                if length is not None:
                    dimensions.append( length )
            dimensions = tuple( dimensions )
            value.__class__.__dimensions__  = dimensions
            return dimensions
    def asArray( self, value, typeCode=None ):
        """Convert given value to an array value of given typeCode"""
        return value
    def unitSize( self, value, typeCode=None ):
        """Determine unit size of an array (if possible)"""
        try:
            return value.__class__.__min_dimension__
        except AttributeError, err:
            dim = self.dims( value )[-1]
            value.__class__.__min_dimension__ = dim
            return dim
    def dimensions( self, value, typeCode=None ):
        """Determine dimensions of the passed array value (if possible)"""
        return tuple( self.dims(value) )


ARRAY_TO_GL_TYPE_MAPPING = {
    constants.GLdouble: constants.GL_DOUBLE,
    constants.GLfloat: constants.GL_FLOAT,
    constants.GLint: constants.GL_INT,
    constants.GLuint: constants.GL_UNSIGNED_INT,
    constants.GLshort: constants.GL_SHORT,
    constants.GLushort: constants.GL_UNSIGNED_SHORT,
        
    constants.GLchar: constants.GL_CHAR,
    constants.GLbyte: constants.GL_BYTE,
    constants.GLubyte: constants.GL_UNSIGNED_BYTE,
}
GL_TYPE_TO_ARRAY_MAPPING = {
    constants.GL_DOUBLE: constants.GLdouble,
    constants.GL_FLOAT: constants.GLfloat,
    constants.GL_INT: constants.GLint,
    constants.GL_UNSIGNED_INT: constants.GLuint,
    constants.GL_SHORT: constants.GLshort,
    constants.GL_UNSIGNED_SHORT: constants.GLushort,
        
    constants.GL_CHAR: constants.GLchar,
    constants.GL_BYTE: constants.GLbyte,
    constants.GL_UNSIGNED_BYTE: constants.GLubyte,
}