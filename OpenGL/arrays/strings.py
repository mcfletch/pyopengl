"""String-array-handling code for PyOpenGL
"""
from OpenGL import constants
from OpenGL.arrays import formathandler
import ctypes
from OpenGL._bytes import bytes

def dataPointer( value, typeCode=None ):
    return ctypes.cast(ctypes.c_char_p(value),
                           ctypes.c_void_p).value

class StringHandler( formathandler.FormatHandler ):
    """String-specific data-type handler for OpenGL"""
    HANDLED_TYPES = (bytes, )
    @classmethod
    def from_param( cls, value, typeCode=None ):
        return ctypes.c_void_p( dataPointer( value ) )
    dataPointer = staticmethod( dataPointer )
    def zeros( self, dims, typeCode=None ):
        """Currently don't allow strings as output types!"""
        raise NotImplemented( """Don't currently support strings as output arrays""" )
    def ones( self, dims, typeCode=None ):
        """Currently don't allow strings as output types!"""
        raise NotImplemented( """Don't currently support strings as output arrays""" )
    def arrayToGLType( self, value ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        raise NotImplemented( """Can't guess data-type from a string-type argument""" )
    def arraySize( self, value, typeCode = None ):
        """Given a data-value, calculate ravelled size for the array"""
        # need to get bits-per-element...
        byteCount = BYTE_SIZES[ typeCode ]
        return len(value)//byteCount
    def arrayByteCount( self, value, typeCode = None ):
        """Given a data-value, calculate number of bytes required to represent"""
        return len(value)
    def asArray( self, value, typeCode=None ):
        """Convert given value to an array value of given typeCode"""
        if isinstance( value, bytes ):
            return value
        elif hasattr( value, 'tostring' ):
            return value.tostring()
        elif hasattr( value, 'raw' ):
            return value.raw
        # could convert types to string here, but we're not registered for
        # anything save string types...
        raise TypeError( """String handler got non-string object: %r"""%(type(value)))
    def dimensions( self, value, typeCode=None ):
        """Determine dimensions of the passed array value (if possible)"""
        raise TypeError(
            """Cannot calculate dimensions for a String data-type"""
        )

BYTE_SIZES = {
    constants.GL_DOUBLE: ctypes.sizeof( constants.GLdouble ),
    constants.GL_FLOAT: ctypes.sizeof( constants.GLfloat ),
    constants.GL_INT: ctypes.sizeof( constants.GLint ),
    constants.GL_SHORT: ctypes.sizeof( constants.GLshort ),
    constants.GL_UNSIGNED_BYTE: ctypes.sizeof( constants.GLubyte ),
    constants.GL_UNSIGNED_SHORT: ctypes.sizeof( constants.GLshort ),
    constants.GL_BYTE: ctypes.sizeof( constants.GLbyte ),
    constants.GL_UNSIGNED_INT: ctypes.sizeof( constants.GLuint ),
}
