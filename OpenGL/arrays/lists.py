"""Lists/tuples as data-format for storage

Note:
    This implementation is *far* less efficient than using Numpy
    to support lists/tuples, as the code here is all available in
    C-level code there.  This implementation is required to allow
    for usage without numpy installed.
"""
REGISTRY_NAME = 'ctypesarrays'
import ctypes, _ctypes

from OpenGL import constants, constant, error
from OpenGL._configflags import ERROR_ON_COPY
from OpenGL.arrays import formathandler
HANDLED_TYPES = (list,tuple)
import operator

def err_on_copy( func ):
    """Decorator which raises informative error if we try to copy while ERROR_ON_COPY"""
    if not ERROR_ON_COPY:
        return func 
    else:
        def raiseErrorOnCopy( self,  value, *args, **named ):
            raise error.CopyError(
                """%s passed, cannot copy with ERROR_ON_COPY set, please use an array type which has native data-pointer support (e.g. numpy or ctypes arrays)"""%( value.__class__.__name__, )
            )
        raiseErrorOnCopy.__name__ = func.__name__
        return raiseErrorOnCopy

class ListHandler( formathandler.FormatHandler ):
    """Storage of array data in Python lists/arrays

    This mechanism, unlike multi-dimensional arrays, is not necessarily
    uniform in type or dimension, so we have to do a lot of extra checks
    to make sure that we get a correctly-structured array.  That, as
    well as the need to copy the arrays in Python code, makes this a far
    less efficient implementation than the numpy implementation, which
    does all the same things, but does them all in C code.

    Note: as an *output* format, this format handler produces ctypes
        arrays, not Python lists, this is done for convenience in coding
        the implementation, mostly.
    """
    @err_on_copy
    def from_param( self, instance, typeCode=None ):
        try:
            return ctypes.byref( instance )
        except TypeError, err:
            array = self.asArray( instance, typeCode )
            pp = ctypes.c_void_p( ctypes.addressof( array ) )
            pp._temporary_array_ = (array,)
            return pp
    dataPointer = staticmethod( ctypes.addressof )
    HANDLED_TYPES = HANDLED_TYPES 
    isOutput = True
    @err_on_copy
    def voidDataPointer( cls, value ):
        """Given value in a known data-pointer type, return void_p for pointer"""
        return ctypes.byref( value )
    def zeros( self, dims, typeCode ):
        """Return array of zeros in given size"""
        type = GL_TYPE_TO_ARRAY_MAPPING[ typeCode ]
        for dim in dims:
            type *= dim 
        return type() # should expicitly set to 0s
    def dimsOf( cls, x ):
        """Calculate total dimension-set of the elements in x
        
        This is *extremely* messy, as it has to track nested arrays
        where the arrays could be different sizes on all sorts of 
        levels...
        """
        try:
            dimensions = [ len(x) ]
        except (TypeError,AttributeError,ValueError), err:
            return []
        else:
            childDimension = None
            for child in x:
                newDimension = cls.dimsOf( child )
                if childDimension is not None:
                    if newDimension != childDimension:
                        raise ValueError( 
                            """Non-uniform array encountered: %s versus %s"""%(
                                newDimension, childDimension,
                            ), x
                        )
    dimsOf = classmethod( dimsOf )

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
        dims = 1
        for base in self.types( value ):
            length = getattr( base, '_length_', None)
            if length is not None:
                dims *= length
        return dims 
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
        for base in self.types( value ):
            length = getattr( base, '_length_', None)
            if length is not None:
                yield length
    @err_on_copy
    def asArray( self, value, typeCode=None ):
        """Convert given value to a ctypes array value of given typeCode
        
        This does a *lot* of work just to get the data into the correct
        format.  It's not going to be anywhere near as fast as a numpy
        or similar approach!
        """
        if typeCode is None:
            raise NotImplementedError( """Haven't implemented type-inference for lists yet""" )
        arrayType = GL_TYPE_TO_ARRAY_MAPPING[ typeCode ]
        if isinstance( value, (list,tuple)):
            subItems = [
                self.asArray( item, typeCode )
                for item in value
            ]
            if subItems:
                for dim in self.dimensions( subItems[0] )[::-1]:
                    arrayType *= dim
                arrayType *= len( subItems )
                result = arrayType()
                result[:] = subItems
                return result
        else:
            return arrayType( value )
    @err_on_copy
    def unitSize( self, value, typeCode=None ):
        """Determine unit size of an array (if possible)"""
        return tuple(self.dims(value))[-1]
    @err_on_copy
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
