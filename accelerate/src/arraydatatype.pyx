"""Cython-coded Array-handling accelerator module"""
#cython: language_level=3

import ctypes
import OpenGL
from OpenGL._null import NULL as _NULL
from OpenGL import plugins
from OpenGL_accelerate.wrapper cimport cArgConverter, pyArgConverter, returnConverter
from OpenGL_accelerate.formathandler cimport FormatHandler

cdef extern from "Python.h":
    cdef object PyObject_Type( object )
    cdef object PyDict_GetItem( object, object )

cdef class HandlerRegistry:
    """C-coded registry of format handlers for array data-formats"""
    cdef dict registry
    cdef object match
    cdef object output_handler
    cdef object preferredOutput
    GENERIC_OUTPUT_PREFERENCES = ['numpy','ctypesarrays']
    cdef object all_output_handlers
    def __init__( self, plugin_match ):
        self.registry = {}
        self.match = plugin_match
        self.output_handler = None 
        self.preferredOutput = None
        self.all_output_handlers = []
    def __setitem__( self,key,value ):
        self.registry[key] = value
    def __call__( self, value ):
        return self.c_lookup( value )
    
    cdef object c_lookup( self, object value ):
        """C-level lookup of handler for given value"""
        cdef object typ, handler,base
        try:
            typ = value.__class__
        except AttributeError as err:
            typ = PyObject_Type(value)
        handler = self.registry.get( typ )
        if not handler:
            if hasattr( typ, '__mro__' ):
                for base in typ.__mro__:
                    handler = self.registry.get( base )
                    if not handler:
                        plugin = self.match( base )
                        if plugin:
                            cls = plugin.load()
                            if cls:
                                handler=cls()
                    if handler:
                        self.registry[ typ ] = handler
                        if hasattr( handler, 'registerEquivalent' ):
                            handler.registerEquivalent( typ, base )
                        return handler
            raise TypeError(
                """No array-type handler for type %r (value: %s) registered"""%(
                    typ, repr(value)[:50]
                )
            )
        return handler
    
    cdef object c_get_output_handler( self ):
        """Fast-path lookup for output handler object"""
        if self.output_handler is None:
            if self.preferredOutput is not None:
                self.output_handler = self.c_handler_by_plugin_name( self.preferredOutput )
            if not self.output_handler:
                for preferred in self.GENERIC_OUTPUT_PREFERENCES:
                    self.output_handler = self.c_handler_by_plugin_name( preferred )
                    if self.output_handler:
                        break
            if not self.output_handler:
                raise RuntimeError(
                    """Unable to find any output handler at all (not even ctypes/numpy ones!)"""
                )
        return self.output_handler
    cdef object c_handler_by_plugin_name( self, str name ):
        plugin = plugins.FormatHandler.by_name( name )
        try:
            handler = plugin.load()
            if handler:
                return handler()
        except ImportError as err:
            return None
    
    def register( self, handler, types=None ):
        """Register this class as handler for given set of types"""
        if not isinstance( types, (list,tuple)):
            types = [ types ]
        for type in types:
            self.registry[ type ] = handler
        if handler.isOutput:
            self.all_output_handlers.append( handler )
        
    def registerReturn( self, handler ):
        """Register this handler as the default return-type handler"""
        if isinstance( handler, (str,unicode)):
            self.preferredOutput = handler 
            self.output_handler = None
        else:
            self.preferredOutput = None 
            self.output_handler = handler

cdef HandlerRegistry GLOBAL_REGISTRY = HandlerRegistry(plugins.FormatHandler.match)

cdef class ArrayDatatype:
    """Mix-in for array datatype classes
    
    The ArrayDatatype marker essentially is used to mark a particular argument
    as having an "array" type, which means that it is eligible for handling 
    via the arrays sub-package and its registered handlers.
    """
    cdef HandlerRegistry handler 
    cdef public object typeConstant
    cdef public object baseType
    isAccelerated = True
    def __init__( self, typeConstant=None, baseType=None ):
        """Initialize, grabbing our handler registry"""
        self.typeConstant = typeConstant
        self.baseType = baseType
        self.handler = GLOBAL_REGISTRY
    
    def getRegistry( self ):
        """Get our handler registry"""
        return self.handler 
    def getHandler( self, value ):
        """Retrieve FormatHandler for given value 
        
        This method is replaced by the FormatHandler registry
        once the registry is initialized...
        """
        return self.handler.c_lookup( value )
    
    def from_param( self, object value, object typeConstant=None ):
        """Given a value in a known data-pointer type, convert to a ctypes pointer"""
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_from_param( 
                value, typeConstant or self.typeConstant 
            )
        return handler.from_param( value, typeConstant or self.typeConstant )
    
    def __call__( self, object value ):
        """We cannot simply reference from_param as under Python 2.7 that makes us non-callable"""
        return self.from_param( value )
    
    def dataPointer( self, value ):
        """Given a value in a known data-pointer type, return long for pointer"""
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_dataPointer( 
                value
            )
        return handler.dataPointer( value )
    def voidDataPointer( self, value ):
        """Given value in a known data-pointer type, return void_p for pointer"""
        pointer = self.dataPointer( value )
        try:
            return ctypes.c_void_p(pointer)
        except TypeError as err:
            return pointer
    def typedPointer( self, value ):
        """Return a pointer-to-base-type pointer for given value"""
        return ctypes.cast( 
            self.dataPointer(value), 
            ctypes.POINTER( self.baseType )
        )
    def asArray( self, value, typeCode=None ):
        """Given a value, convert to preferred array representation"""
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_asArray( 
                value, typeCode 
            )
        return handler.asArray( 
            value, typeCode
        )
    def arrayToGLType( self, value ):
        """Given a data-value, guess the OpenGL type of the corresponding pointer
        
        Note: this is not currently used in PyOpenGL and may be removed 
        eventually.
        """
        return self.handler.c_lookup( value ).arrayToGLType( value )
    def arraySize( self, value, typeCode = None ):
        """Given a data-value, calculate dimensions for the array (number-of-units)"""
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_arraySize( 
                value, typeCode 
            )
        return handler.arraySize( 
            value, typeCode
        )
    def unitSize( self, value, typeCode=None ):
        """Determine unit size of an array (if possible)
        
        Uses our local type if defined, otherwise asks the handler to guess...
        """
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_unitSize( 
                value, typeCode 
            )
        return handler.unitSize( 
            value, typeCode
        )
    def returnHandler( self ):
        """Get the default return-handler"""
        return self.handler.c_get_output_handler( )
    def zeros( self, dims, typeCode=None ):
        """Allocate a return array of the given dimensions filled with zeros"""
        return self.c_zeros( dims, typeCode )
    cdef c_zeros( self, dims, typeCode ):
        """C-level function to create empty array"""
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_get_output_handler( )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_zeros( 
                dims, typeCode 
            )
        return handler.zeros( 
            dims, typeCode
        )
        
        
    def dimensions( self, value, typeCode=None ):
        """Given a data-value, get the dimensions (assumes full structure info)"""
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_dimensions( 
                value
            )
        return handler.dimensions( value )
    
    def arrayByteCount( self, value, typeCode=None ):
        """Given a data-value, try to determine number of bytes it's final form occupies
        
        For most data-types this is arraySize() * atomic-unit-size
        """
        if typeCode is None:
            typeCode = self.typeConstant
        handler = self.handler.c_lookup( value )
        if isinstance( handler, FormatHandler ):
            return (<FormatHandler>handler).c_arrayByteCount( 
                value
            )
        return handler.arrayByteCount( value )

# Now some array helper functions...

cdef class Output(cArgConverter):
    """CConverter generating static-size typed output arrays
    
    Produces an output array of given type (arrayType) and 
    size using self.lookup() to determine the size of the 
    array to be produced, where the lookup function is passed 
    as an initialisation argument.
    
    Provides also:
    
        oldStyleReturn( ... ) for use in the default case of
            PyOpenGL compatability mode, where result arrays of
            size (1,) are returned as scalar values.
    """
    cdef str name 
    cdef tuple size
    cdef ArrayDatatype arrayType
    cdef int outIndex
    def __init__( self, str name, tuple size, ArrayDatatype arrayType ):
        self.name = name 
        self.size = size 
        self.arrayType = arrayType
    def finalise( self, wrapper ):
        self.outIndex = wrapper.cArgIndex( self.name )
        
    cdef tuple c_getSize( self, tuple pyArgs ):
        """Retrieve the array size for this argument"""
        return self.size
    
    cdef object c_call( self, tuple pyArgs, int index, object baseOperation ):
        """Return pyArgs[ self.index ]"""
        return self.arrayType.c_zeros( self.c_getSize(pyArgs), self.arrayType.typeConstant )

    cdef object c_orInput( self, tuple pyArgs, int index ):
        """Coerce a passed-in output array, refusing a lossy copy.

        When the caller's array is already an acceptable buffer, asArray returns
        it unchanged and the GL result is written straight back into it. When it
        is the wrong type, asArray must *copy* it to match; if that copy is
        smaller than the caller's buffer, the read is truncated into the copy and
        never reaches the caller's array -- the silent "returns zeroes" bug.
        Detect the shrinking copy and raise. Correctly-typed arrays are not
        copied, so they never trip this.

        Then the other question, which the count answers: an array shorter than
        the call will write into is a heap overrun rather than an exception, so
        it is refused. See ``Output.checkOutputSize`` in OpenGL/converters.py,
        which is the same check for the pure-Python converter -- this one is
        what runs where accelerate is installed, whichever dispatch layer the
        entry points come from.
        """
        value = pyArgs[index]
        result = self.arrayType.asArray( value )
        if result is not value:
            try:
                rbytes = self.arrayType.arrayByteCount( result )
                vbytes = self.arrayType.arrayByteCount( value )
            except Exception:
                # Not measurable -- a list has no byte count of its own -- so
                # there is no shrinking coercion to detect. The size the call
                # will write is still checked below.
                rbytes = vbytes = 0
            if rbytes < vbytes:
                raise TypeError(
                    '%s: pass-in output array was coerced to a smaller buffer '
                    '(%d < %d bytes), so the GL result cannot be written back '
                    'into your array. Pass a correctly-typed array, or None to '
                    'have one allocated.' % ( self.name, rbytes, vbytes )
                )
        self.c_checkOutputSize( result, pyArgs )
        return result

    cdef int c_checkOutputSize( self, object array, tuple pyArgs ) except -1:
        """Nothing to check: a fixed declared size is a maximum.

        Which of it a call fills depends on the pname -- glGetVertexAttribiv
        declares four and writes one for most of them -- so a shorter array is
        legitimate here.  :class:`SizedOutput` overrides this, because its size
        is a count the caller passed and so says what will be written.
        """
        return 0

    cdef int c_checkPromisedSize( self, object array, tuple pyArgs ) except -1:
        """Refuse an output array smaller than the call will write into it.

        Only a shortfall: a larger array is a caller deliberately reusing one
        buffer for several calls, which is ordinary and safe.
        """
        cdef long wanted = 1
        try:
            shape = self.c_getSize( pyArgs )
        except Exception:
            return 0
        if shape is None:
            return 0
        for dimension in shape:
            try:
                wanted = wanted * int(dimension)
            except (TypeError, ValueError):
                return 0
        if wanted <= 0:
            return 0
        # Compared in bytes, not elements.  The count is in units of the type
        # the *declaration* names -- glGetBufferSubData's `size` is a byte
        # count, glGenTextures' `n` is a count of GLuint -- and the caller may
        # pass an array of some other type holding the same bytes.
        # Only what carries its own length.  A bare ctypes pointer does not --
        # the hand-written wrappers in OpenGL/GL/exceptional.py pass
        # `typedPointer` results straight down -- and arrayByteCount answers
        # for one anyway, with the size of a single element.
        if not hasattr( array, '__len__' ):
            return 0
        try:
            wanted_bytes = wanted * ctypes.sizeof( self.arrayType.baseType )
            held_bytes = self.arrayType.arrayByteCount( array )
        except Exception:
            return 0
        if held_bytes < wanted_bytes:
            raise ValueError(
                '%s: output array holds %d byte(s), but the call will '
                'write %d. Pass a larger array, or None to have one '
                'allocated.' % ( self.name, held_bytes, wanted_bytes )
            )
        return 0

    def oldStyleReturn( self, object result, object baseOperation, tuple pyArgs, tuple cArgs ):
        """Retrieve cArgs[ self.index ]"""
        #TODO: make this a c_api-bearing value, not a Python function call
        cdef tuple thisSize
        result = cArgs[ self.outIndex ]
        try:
            thisSize = self.c_getSize(pyArgs)
        except KeyError as err:
            return result
        if thisSize == (1,):
            try:
                return result[0]
            except (IndexError,TypeError) as err:
                return result
        else:
            return result
cdef class OutputOrInput( Output ):
    cdef object c_call( self, tuple pyArgs, int index, object baseOperation ):
        """Return pyArgs[ self.index ]"""
        if pyArgs[index] is not DO_OUTPUT[0] and pyArgs[index] is not DO_OUTPUT[1]:
            return self.c_orInput( pyArgs, index )
        return self.arrayType.c_zeros( self.c_getSize(pyArgs), self.arrayType.typeConstant )

cdef class SizedOutput( Output ):
    """Output class that looks up output size via a callable function
    
    specifier -- Python argument name used to lookup the data-size 
    lookup -- function taking argument in specifier to determine size 
    """
    cdef str specifier
    cdef object lookup
    cdef int index 
    
    def __init__( self, str name, str specifier, object lookup, ArrayDatatype arrayType ):
        super( SizedOutput,self).__init__( name, None, arrayType )
        self.specifier = specifier
        self.lookup = lookup
        self.arrayType = arrayType
    def finalise( self, wrapper ):
        super( SizedOutput,self).finalise( wrapper )
        self.index = wrapper.pyArgIndex( self.specifier )
    cdef int c_checkOutputSize( self, object array, tuple pyArgs ) except -1:
        """Check the size only where it says what this call will write.

        It does when it comes from a *count* the caller passed --
        glGenTextures(n, names) writes n, glGetBufferSubData writes `size`
        bytes -- which the declaration spells `size=lambda x: (x,)`.

        It does not when it comes from a table keyed on a *pname*, which says
        how large that piece of state is in total; how much of it a call fills
        is the call's business, and glGetIntegeri_v writes one element of a
        three-element pname at a time.  The declaration spells that
        `size=<a dict>`, handed on as its `__getitem__` -- so the dict it is
        bound to is what tells the two apart.
        """
        if isinstance( getattr( self.lookup, '__self__', None ), dict ):
            return 0
        return self.c_checkPromisedSize( array, pyArgs )

    cdef tuple c_getSize( self, tuple pyArgs ):
        """Retrieve the array size for this argument"""
        try:
            specifier = pyArgs[ self.index ]
        except AttributeError as err:
            raise RuntimeError( """"Did not resolve parameter index for %r"""%(self.name))
        else:
            try:
                result =  self.lookup( specifier )
                if not isinstance( result, tuple ):
                    result = (result,)
                return result
            except (TypeError,KeyError) as err:
                raise KeyError( """Unknown specifier %r (lookup = %s)"""%( specifier, self.lookup ))
DO_OUTPUT = (None,_NULL)
cdef class SizedOutputOrInput( SizedOutput ):
    cdef object c_call( self, tuple pyArgs, int index, object baseOperation ):
        """Return pyArgs[ self.index ]"""
        if pyArgs[index] is not DO_OUTPUT[0] and pyArgs[index] is not DO_OUTPUT[1]:
            return self.c_orInput( pyArgs, index )
        return self.arrayType.c_zeros( self.c_getSize(pyArgs), self.arrayType.typeConstant )
    

cdef class AsArrayOfType(pyArgConverter):
    """Given arrayName and typeName coerce arrayName to array of type typeName
    
    TODO: It should be possible to drop this if ERROR_ON_COPY,
    as array inputs always have to be the final objects in that 
    case.
    """
    cdef public str arrayName
    cdef public str typeName
    
    cdef int arrayIndex
    cdef int typeIndex
    cdef public ArrayDatatype arrayType
    
    def __init__( self, str arrayName='pointer', str typeName='type' ):
        self.arrayName = arrayName
        self.typeName = typeName 
        from OpenGL.arrays.arraydatatype import ArrayDatatype
        self.arrayType = ArrayDatatype
    def finalise( self, wrapper ):
        self.arrayIndex = wrapper.pyArgIndex( self.arrayName )
        self.typeIndex = wrapper.pyArgIndex( self.typeName )
    cdef object c_call( self, object incoming, object function, tuple arguments ):
        """Get the arg as an array of the appropriate type"""
        return self.arrayType.asArray( incoming, arguments[ self.typeIndex ] )

cdef class AsArrayTyped(pyArgConverter):
    """Given arrayName and arrayType, convert arrayName to array of type
    
    TODO: It should be possible to drop this if ERROR_ON_COPY,
    as array inputs always have to be the final objects in that 
    case.
    """
    cdef public str arrayName
    cdef int arrayIndex
    cdef public ArrayDatatype arrayType
    def __init__( self, arrayName='pointer', arrayType=None ):
        self.arrayName = arrayName # not actually used...
        if arrayType is None:
            from OpenGL.arrays.arraydatatype import ArrayDatatype
            arrayType = ArrayDatatype
        self.arrayType = arrayType
    def finalise( self, wrapper ):
        """Finalize the wrapper (nothing to do here)"""
    cdef object c_call( self, object incoming, object function, tuple arguments ):
        """Get the arg as an array of the appropriate type"""
        return self.arrayType.asArray( incoming )

cdef class AsArrayTypedSizeChecked( AsArrayTyped ):
    """Size-checking version of AsArrayTyped"""
    cdef int size 
    def __init__( self, arrayType=None, size=None ):
        super(AsArrayTypedSizeChecked,self).__init__( 'pointer', arrayType )
        baseSize = ctypes.sizeof( arrayType.baseType )
        self.size = size * baseSize
    cdef object c_call( self, object incoming, object function, tuple arguments ):
        """Get the arg as an array of the appropriate type"""
        cdef int actualSize
        result = self.arrayType.asArray( incoming )
        actualSize = self.arrayType.arrayByteCount( result )
        if actualSize != self.size:
            raise ValueError(
                """Expected %r byte array, got %r byte array"""%(
                    self.size,
                    actualSize,
                ),
                incoming,
            )
        return result
    
cdef class AsArrayTypedSize(cArgConverter):
    """Given arrayName and arrayType, determine size of arrayName
    """
    cdef public str arrayName
    cdef int arrayIndex
    cdef public ArrayDatatype arrayType
    
    def __init__( self, arrayName='pointer', arrayType=None ):
        self.arrayName = arrayName
        if arrayType is None:
            from OpenGL.arrays.arraydatatype import ArrayDatatype
            arrayType = ArrayDatatype
        self.arrayType = arrayType
    def finalise( self, wrapper ):
        self.arrayIndex = wrapper.pyArgIndex( self.arrayName )
    cdef c_call( self, tuple pyArgs, int index, object wrappedOperation ):
        return self.arrayType.arraySize( pyArgs[self.arrayIndex ] )

