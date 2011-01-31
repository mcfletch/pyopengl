"""Array data-type implementations (abstraction points for GL array types"""
import ctypes
import OpenGL
from OpenGL import constants, plugins
from OpenGL.arrays import formathandler
from OpenGL import logs
log = logs.getLog( 'OpenGL.arrays.arraydatatype' )


from OpenGL import acceleratesupport
ADT = None
if acceleratesupport.ACCELERATE_AVAILABLE:
    try:
        from OpenGL_accelerate.arraydatatype import ArrayDatatype as ADT
    except ImportError, err:
        log.warn(
            "Unable to load ArrayDatatype accelerator from OpenGL_accelerate"
        )
if ADT is None:
    # Python-coded version
    class HandlerRegistry( dict ):
        GENERIC_OUTPUT_PREFERENCES = ['numpy','numeric','ctypesarrays']
        def __init__( self, plugin_match ):
            self.match = plugin_match
            self.output_handler = None 
            self.preferredOutput = None
            self.all_output_handlers = []
        def __call__( self, value ):
            """Lookup of handler for given value"""
            try:
                typ = value.__class__
            except AttributeError, err:
                typ = type(value)
            handler = self.get( typ )
            if not handler:
                if hasattr( typ, '__mro__' ):
                    for base in typ.__mro__:
                        handler = self.get( base )
                        if not handler:
                            handler = self.match( base )
                            if handler:
                                handler = handler.load()
                                if handler:
                                    handler = handler()
                        if handler:
                            self[ typ ] = handler
                            if hasattr( handler, 'registerEquivalent' ):
                                handler.registerEquivalent( typ, base )
                            return handler
                raise TypeError(
                    """No array-type handler for type %r (value: %s) registered"""%(
                        typ, repr(value)[:50]
                    )
                )
            return handler
        
        def get_output_handler( self ):
            """Fast-path lookup for output handler object"""
            if self.output_handler is None:
                if not self:
                    formathandler.FormatHandler.loadAll()
                if self.preferredOutput is not None:
                    self.output_handler = self.get( self.preferredOutput )
                if not self.output_handler:
                    for preferred in self.GENERIC_OUTPUT_PREFERENCES:
                        self.output_handler = self.get( preferred )
                        if self.output_handler:
                            break
                if not self.output_handler:
                    # look for anything that can do output...
                    for handler in self.all_output_handlers:
                        self.output_handler = handler 
                        break
                if not self.output_handler:
                    raise RuntimeError(
                        """Unable to find any output handler at all (not even ctypes/numpy ones!)"""
                    )
            return self.output_handler
        
        def register( self, handler, types=None ):
            """Register this class as handler for given set of types"""
            if not isinstance( types, (list,tuple)):
                types = [ types ]
            for type in types:
                self[ type ] = handler
            if handler.isOutput:
                self.all_output_handlers.append( handler )
            
        def registerReturn( self, handler ):
            """Register this handler as the default return-type handler"""
            self.preferredOutput = handler 
            self.output_handler = None
    
    GLOBAL_REGISTRY = HandlerRegistry( plugins.FormatHandler.match)
    formathandler.FormatHandler.TYPE_REGISTRY = GLOBAL_REGISTRY
    
    class ArrayDatatype( object ):
        """Mix-in for array datatype classes
        
        The ArrayDatatype marker essentially is used to mark a particular argument
        as having an "array" type, which means that it is eligible for handling 
        via the arrays sub-package and its registered handlers.
        """
        typeConstant = None
        handler = GLOBAL_REGISTRY
        getHandler = GLOBAL_REGISTRY.__call__
        returnHandler = GLOBAL_REGISTRY.get_output_handler
        isAccelerated = False
        @classmethod
        def getRegistry( cls ):
            """Get our handler registry"""
            return cls.handler 
        def from_param( cls, value ):
            """Given a value in a known data-pointer type, convert to a ctypes pointer"""
            return cls.getHandler(value).from_param( value, cls.typeConstant )
        from_param = classmethod( logs.logOnFail( from_param, log ) )
        def dataPointer( cls, value ):
            """Given a value in a known data-pointer type, return long for pointer"""
            try:
                return cls.getHandler(value).dataPointer( value )
            except Exception, err:
                log.warn(
                    """Failure in dataPointer for %s instance %s""", type(value), value,
                )
                raise
        dataPointer = classmethod( logs.logOnFail( dataPointer, log ) )
        def voidDataPointer( cls, value ):
            """Given value in a known data-pointer type, return void_p for pointer"""
            pointer = cls.dataPointer( value )
            try:
                return ctypes.c_void_p(pointer)
            except TypeError, err:
                return pointer
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
            """Given a data-value, guess the OpenGL type of the corresponding pointer
            
            Note: this is not currently used in PyOpenGL and may be removed 
            eventually.
            """
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
    
    class GLint64Array( ArrayDatatype, ctypes.POINTER(constants.GLint64 )):
        """Array datatype for GLuint types"""
        baseType = constants.GLint64
        typeConstant = None # TODO: find out what this should be!
    
    class GLuint64Array( ArrayDatatype, ctypes.POINTER(constants.GLuint64 )):
        """Array datatype for GLuint types"""
        baseType = constants.GLuint64
        typeConstant = constants.GL_UNSIGNED_INT64

    class GLenumArray( ArrayDatatype, ctypes.POINTER(constants.GLenum )):
        """Array datatype for GLenum types"""
        baseType = constants.GLenum
        typeConstant = constants.GL_UNSIGNED_INT
    class GLsizeiArray( ArrayDatatype, ctypes.POINTER(constants.GLsizei )):
        """Array datatype for GLenum types"""
        baseType = constants.GLsizei
        typeConstant = constants.GL_INT
    class GLvoidpArray( ArrayDatatype, ctypes.POINTER(constants.GLvoid )):
        """Array datatype for GLenum types"""
        baseType = constants.GLvoidp
        typeConstant = constants.GL_VOID_P
else:
    # Cython-coded array handler
    log.info( 'Using accelerated ArrayDatatype' )
    ArrayDatatype = ADT( None, None )
    GLclampdArray = ADT( constants.GL_DOUBLE, constants.GLclampd )
    GLclampfArray = ADT( constants.GL_FLOAT, constants.GLclampf )
    GLdoubleArray = ADT( constants.GL_DOUBLE, constants.GLdouble )
    GLfloatArray = ADT( constants.GL_FLOAT, constants.GLfloat )
    GLbyteArray = ADT( constants.GL_BYTE, constants.GLbyte )
    GLcharArray = GLcharARBArray = ADT( constants.GL_BYTE, constants.GLchar )
    GLshortArray = ADT( constants.GL_SHORT, constants.GLshort )
    GLintArray = ADT( constants.GL_INT, constants.GLint )
    GLubyteArray = GLbooleanArray = ADT( constants.GL_UNSIGNED_BYTE, constants.GLubyte )
    GLushortArray = ADT( constants.GL_UNSIGNED_SHORT, constants.GLushort )
    GLuintArray = ADT( constants.GL_UNSIGNED_INT, constants.GLuint )
    GLint64Array = ADT( None, constants.GLint64 )
    GLuint64Array = ADT( constants.GL_UNSIGNED_INT64, constants.GLuint64 )
    GLenumArray = ADT( constants.GL_UNSIGNED_INT, constants.GLenum )
    GLsizeiArray = ADT( constants.GL_INT, constants.GLsizei )
    GLvoidpArray = ADT( constants.GL_VOID_P, constants.GLvoidp )

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
