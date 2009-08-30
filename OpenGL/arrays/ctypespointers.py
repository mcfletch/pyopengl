"""ctypes data-pointers as a data-format mechanism
"""
REGISTRY_NAME = 'ctypespointers'
import ctypes, _ctypes

from OpenGL import constants, constant
from OpenGL.arrays import formathandler
import operator

class CtypesPointerHandler( formathandler.FormatHandler ):
    """Ctypes Pointer-type-specific data-type handler for OpenGL
    
    Because pointers do not have size information we can't use
    them for output of data, but they can be used for certain
    types of input...
    """
    @classmethod
    def from_param( cls, value, typeCode=None  ):
        return value
    dataPointer = staticmethod( ctypes.addressof )
    HANDLED_TYPES = (ctypes._Pointer, )
    def voidDataPointer( cls, value ):
        """Given value in a known data-pointer type, return void_p for pointer"""
        return ctypes.cast( value, ctypes.c_void_p )
    def zeros( self, dims, typeCode ):
        """Return Numpy array of zeros in given size"""
        raise NotImplementedError( """Sized output doesn't yet work...""" )
    def ones( self, dims, typeCode='d' ):
        """Return numpy array of ones in given size"""
        raise NotImplementedError( """Haven't got a good ones implementation yet""" )
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
        raise NotImplementedError( """Haven't got an arraySize implementation""" )
    def asArray( self, value, typeCode=None ):
        """Convert given value to an array value of given typeCode"""
        return value
    def unitSize( self, value, typeCode=None ):
        """Determine unit size of an array (if possible)"""
        return 1
    def dimensions( self, value, typeCode=None ):
        """Determine dimensions of the passed array value (if possible)"""
        raise NotImplementedError( """Haven't got a dimensions implementation""" )


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