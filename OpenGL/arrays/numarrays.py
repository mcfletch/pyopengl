"""NumArray implementation of the OpenGL-ctypes array interfaces
"""
REGISTRY_NAME = 'numarray'
try:
    import numarray
except ImportError, err:
    raise ImportError( """No numarray module present: %s"""%(err))
import operator

from OpenGL.arrays import numericnames
implementationModuleName = numericnames.moduleName( numarray )
try:
    implementationModule = numericnames.loadModule( implementationModuleName )
except ImportError, err:
    raise ImportError( """Do not have implementation module %s for current numpy module"""%(
        implementationModuleName,
    ))
dataPointer = implementationModule.dataPointer

from OpenGL import constants, constant
from OpenGL.arrays import formathandler

class NumarrayHandler( formathandler.FormatHandler ):
    """Numarray-specific data-type handler for OpenGL"""
    @classmethod
    def from_param( cls, value, typeCode=None ):
        return dataPointer( value )
    dataPointer = staticmethod( dataPointer )
    HANDLED_TYPES = (numarray.ArrayType, )
    isOutput = True

    def voidDataPointer( cls, value ):
        """Given value in a known data-pointer type, return void_p for pointer"""
        return ctypes.c_void_p( self.dataPointer( value ))
    def zeros( self, dims, typeCode ):
        """Return Numpy array of zeros in given size"""
        return numarray.zeros( dims, GL_TYPE_TO_ARRAY_MAPPING.get(typeCode) or typeCode )
    def arrayToGLType( self, value ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        typeCode = value.typecode()
        constant = ARRAY_TO_GL_TYPE_MAPPING.get( typeCode )
        if constant is None:
            raise TypeError(
                """Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
                    typeCode, ARRAY_TO_GL_TYPE_MAPPING.keys(), value,
                )
            )
        return constant
    def arraySize( self, value, typeCode = None ):
        """Given a data-value, calculate dimensions for the array"""
        try:
            dimValue = value.shape
        except AttributeError, err:
            # XXX it's a list or a tuple, how do we determine dimensions there???
            # for now we'll just punt and convert to an array first...
            value = self.asArray( value, typeCode )
            dimValue = value.shape 
        dims = 1
        for dim in dimValue:
            dims *= dim 
        return dims 
    def asArray( self, value, typeCode=None ):
        """Convert given value to an array value of given typeCode"""
        if value is None:
            return value
        else:
            return self.contiguous( value, typeCode )

    def contiguous( self, source, typeCode=None ):
        """Get contiguous array from source
        
        source -- numarray Python array (or compatible object)
            for use as the data source.  If this is not a contiguous
            array of the given typeCode, a copy will be made, 
            otherwise will just be returned unchanged.
        typeCode -- optional 1-character typeCode specifier for
            the numarray.array function.
            
        All gl*Pointer calls should use contiguous arrays, as non-
        contiguous arrays will be re-copied on every rendering pass.
        Although this doesn't raise an error, it does tend to slow
        down rendering.
        """
        typeCode = GL_TYPE_TO_ARRAY_MAPPING[ typeCode ]
        if isinstance( source, numarray.ArrayType):
            if source.iscontiguous() and (typeCode is None or typeCode==source.typecode()):
                return source
            else:
                # We have to do astype to avoid errors about unsafe conversions
                # XXX Confirm that this will *always* create a new contiguous array 
                # XXX Allow a way to make this raise an error for performance reasons
                # XXX Guard against wacky conversion types like uint to float, where
                # we really don't want to have the C-level conversion occur.
                return numarray.array( source.astype( typeCode ), typeCode )
        elif typeCode:
            return numarray.array( source, typeCode )
        else:
            return numarray.array( source )
    def unitSize( self, value, typeCode=None ):
        """Determine unit size of an array (if possible)"""
        return value.shape[-1]
    def dimensions( self, value, typeCode=None ):
        """Determine dimensions of the passed array value (if possible)"""
        return value.shape


ARRAY_TO_GL_TYPE_MAPPING = {
    'd': constants.GL_DOUBLE,
    'f': constants.GL_FLOAT,
    'i': constants.GL_INT,
    's': constants.GL_SHORT,
    'c': constants.GL_UNSIGNED_BYTE,
    'b': constants.GL_BYTE,
    'I': constants.GL_UNSIGNED_INT,
}
GL_TYPE_TO_ARRAY_MAPPING = {
    constants.GL_DOUBLE: 'd',
    constants.GL_FLOAT:'f',
    constants.GL_INT: 'i',
    constants.GL_UNSIGNED_INT: 'i',
    constants.GL_UNSIGNED_BYTE: 'c',
    constants.GL_SHORT: 's',
    constants.GL_UNSIGNED_SHORT: 's',
    constants.GL_BYTE: 'b',
}