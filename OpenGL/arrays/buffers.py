#! /usr/bin/env python
"""Test for a buffer-protocol-based access mechanism

Will *only* work for Python 2.6+, and pretty much just works for strings
under 2.6 (in terms of the common object types).
"""
import ctypes,sys
from OpenGL.arrays import _buffers
from OpenGL import constants
from OpenGL.arrays import formathandler

class BufferHandler( formathandler.FormatHandler ):
    """Buffer-protocol data-type handler for OpenGL"""
    HANDLED_TYPES = (bytes,bytearray)
    @classmethod
    def from_param( cls, value, typeCode=None ):
        if not isinstance( value, _buffers.Py_buffer ):
            raise TypeError( """Can't convert value to py-buffer in from_param""" )
        return value.buf
    dataPointer = staticmethod( dataPointer )
    def zeros( self, dims, typeCode=None ):
        """Currently don't allow strings as output types!"""
        return self.asArray( bytearray( b'\000'*reduce(operator.mul,dims)*BYTE_SIZES[typeCode] ) )
    def ones( self, dims, typeCode=None ):
        """Currently don't allow strings as output types!"""
        raise NotImplemented( """Have not implemented ones for buffer type""" )
    def arrayToGLType( self, value ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        raise NotImplemented( """Can't guess data-type from a string-type argument""" )
    def arraySize( self, value, typeCode = None ):
        """Given a data-value, calculate ravelled size for the array"""
        # need to get bits-per-element...
        # TODO: verify that multi-dim gives ravelled for buffer API
        return value.len
    def arrayByteCount( self, value, typeCode = None ):
        """Given a data-value, calculate number of bytes required to represent"""
        return value.len * value.itemsize
    def asArray( self, value, typeCode=None ):
        """Convert given value to an array value of given typeCode"""
        if not CheckBuffer( value ):
            raise TypeError( """Require a type which supports the buffer protocol, %s doesn't"""%( type(value)))
        buf = Py_buffer()
        GetBuffer( value, buf, PyBUF_CONTIG_RO )
        return buf
    def dimensions( self, value, typeCode=None ):
        """Determine dimensions of the passed array value (if possible)"""
        return value.dims

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
