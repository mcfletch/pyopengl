"""Cython-coded VBO implementation"""
import ctypes, weakref
from OpenGL_accelerate.formathandler cimport FormatHandler
from OpenGL import error

cdef extern from "Python.h":
    cdef void Py_XINCREF( object )
    cdef void Py_XDECREF( object )

_NULL = object()

cdef class VBO:
    """Instances can be passed into array-handling routines

    You can check for whether VBOs are supported by accessing the implementation
    attribute of the VBO, which will raise a RuntimeError if there is no available
    implementation.

    Attributes:

        int copied -- whether we are copied to back-end yet
        int created -- whether we've created a buffer yet
        unsigned int buffer -- our buffer once created
        object data -- our data-holding array-compatible object
        target -- our resolved GL constant target
        target_spec -- our (unresolved) GL constant specifier
        usage -- our resolved GL constant usage
        usage_spec -- our (unresolved) GL constant usage specifier
        _copy_segments -- slices of data to copy to back-end
        _I_ -- our implementation object
        arrayType -- our reference to arraydatatype.ArrayDatatype
    """
    cdef object __weakref__ # allow weak-referencing for cleanups...
    cdef public int copied
    cdef public int created
    cdef public unsigned int buffer
    cdef public object data
    cdef public int size
    cdef public object target
    cdef public object usage
    cdef public int resolved
    cdef public object target_spec # possible string definition
    cdef public object usage_spec # possible string definition
    cdef public list _copy_segments
    cdef public object _I_
    cdef public object arrayType
    _no_cache_ = True # do not cache in context data arrays
    def __init__(
        self, data, usage='GL_DYNAMIC_DRAW',
        target='GL_ARRAY_BUFFER',
        size=None,
    ):
        """Initialize the VBO

        data -- array-compatible data format object

        usage -- string/GLenum constant specifying streaming usage
            for the VBO, normal values:

                GL_STREAM_DRAW -- updated every frame from client to card
                GL_STREAM_COPY -- read and written from card each frame

                GL_STATIC_DRAW -- just written from client (once)
                GL_STATIC_READ -- just read from client
                GL_STATIC_COPY -- read and written from client (once)

                GL_DYNAMIC_DRAW -- updated from client every once in a while
                GL_DYNAMIC_COPY -- read and written from client every once in a while
                GL_DYNAMIC_READ -- read from the client every once in a while

        target -- string/GLenum constant specifying the role for the buffer
            normal values:

                GL_ARRAY_BUFFER -- vertex attribute values
                GL_ELEMENT_ARRAY_BUFFER -- vertex index values
                GL_PIXEL_PACK_BUFFER/GL_PIXEL_UNPACK_BUFFER -- client-side
                    image source/sink for image-manipulation operations.
        """
        from OpenGL.arrays.arraydatatype import ArrayDatatype
        self.arrayType = ArrayDatatype
        self.c_set_array( data, size )
        self.resolved = self.created = self.copied = False
        self.usage_spec = usage
        self.target_spec = target
        self._copy_segments = []
        self._I_ = None
    def __dealloc__( self ):
        """Deallocate our references"""
        if self.data is not None:
            Py_XDECREF( self.data )
            self.data = None
    @property
    def implementation( self ):
        """Retrieve our implementation reference"""
        return self.get_implementation()
    cdef get_implementation( self ):
        """C-level implementation retrieval"""
        if self._I_ is None:
            from OpenGL.arrays.vbo import get_implementation
            self._I_ = get_implementation()
        return self._I_
    cdef unsigned int c_resolve( self, value ):
        """Resolve string constant to constant"""
        if isinstance( value, (str,unicode)):
            return getattr(
                self.get_implementation(),
                self.get_implementation().basename( value )
            )
        return value
    def set_array( self, data, size=None ):
        """Update our entire array with new data"""
        return self.c_set_array( data, size )
    cdef c_set_array( self, data, size ):
        """Set our array pointer with incref/decref support"""
        if self.data is not None:
            Py_XDECREF( self.data )
        Py_XINCREF( data )
        self.data = data
        if size is None and self.data is not None:
            size = self.arrayType.arrayByteCount( self.data )
        self.size = size
        self.copied = False
    def __setitem__( self, slice, array):
        """Set slice of data on the array and vbo (if copied already)

        slice -- the Python slice object determining how the data should
            be copied into the vbo/array
        array -- something array-compatible that will be used as the
            source of the data, note that the data-format will have to
            be the same as the internal data-array to work properly, if
            not, the amount of data copied will be wrong.

        This is a reasonably complex operation, it has to have all sorts
        of state-aware changes to correctly map the source into the low-level
        OpenGL view of the buffer (which is just bytes as far as the GL
        is concerned).
        """
        if slice.step and not slice.step == 1:
            raise NotImplemented( """Don't know how to map stepped arrays yet""" )
        # TODO: handle e.g. mapping character data into an integer data-set
        data = self.arrayType.asArray( array )
        start = (slice.start or 0)
        stop = (slice.stop or len(self.data))
        if start < 0:
            start += len(self.data)
            start = max((start,0))
        if stop < 0:
            stop += len(self.data)
            stop = max((stop,0))
        self.data[ slice ] = data
        if self.copied and self.created:
            if start-stop != len(data):
                self.copied = False
            elif start-stop == len(self.data):
                # re-copy the whole data-set
                self.copied = False
            elif len(data):
                # now the fun part, we need to make the array match the
                # structure of the array we're going to copy into and make
                # the "size" parameter match the value we're going to copy in,
                # note that a 2D array (rather than a 1D array) may require
                # multiple mappings to copy into the memory area...

                # find the step size from the dimensions and base size...
                size = self.arrayType.arrayByteCount( data ) / len(array)
                #baseSize = self.arrayType.unitSize( data )
                # now create the start and distance values...
                start *= size
                stop *= size
                # wait until the last moment (bind) to copy the data...
                self._copy_segments.append(
                    (start,(stop-start), data)
                )
    def __len__( self ):
        return len( self.data )
    def __getattr__( self, key ):
        if key not in ('data','usage','target','buffer', 'copied','_I_','implementation','_copy_segments' ):
            return getattr( self.data, key )
        else:
            raise AttributeError( key )
    def create_buffers( self ):
        """Create the internal buffer(s)"""
        assert not self.created, """Already created the buffer"""
        buffers = self.get_implementation().glGenBuffers(1)
        try:
            self.buffer = long( buffers )
        except (TypeError,ValueError), err:
            self.buffer = buffers[0]
        self.target = self.c_resolve( self.target_spec )
        self.usage = self.c_resolve( self.usage_spec )
        self.created = True
        self.get_implementation()._DELETERS_[ id(self) ] = weakref.ref(
            # Cython instances can't have weakrefs, sigh...
            self,
            self.get_implementation().deleter( [self.buffer], id(self) )
        )
        return self.buffer
    def copy_data( self ):
        """Copy our data into the buffer on the GL side"""
        assert self.created, """Should do create_buffers before copy_data"""
        if self.copied:
            if self._copy_segments:
                while self._copy_segments:
                    start,size,data  = self._copy_segments.pop(0)
                    dataptr = self.arrayType.voidDataPointer( data )
                    self.get_implementation().glBufferSubData(self.target, start, size, dataptr)
        else:
            self.get_implementation().glBufferData(
                self.target,
                self.size,
                self.data,
                self.usage,
            )
            self.copied = True
    def delete( self ):
        """Delete this buffer explicitly"""
        if self.created:
            self.created = False
            try:
                self.get_implementation().glDeleteBuffers(1, ctypes.c_uint32( self.buffer))
            except (AttributeError, error.NullFunctionError), err:
                pass
            try:
                self.get_implementation()._DELETERS_.pop( id(self))
            except KeyError, err:
                pass
    def bind( self ):
        """Bind this buffer for use in vertex calls"""
        if not self.created:
            buffer = self.create_buffers()
        self.get_implementation().glBindBuffer( self.target, self.buffer)
        self.copy_data()
    def unbind( self ):
        """Unbind the buffer (make normal array operations active)"""
        self.get_implementation().glBindBuffer( self.target,0 )
    def __add__( self, other ):
        """Add an integer to this VBO (offset)"""
        if hasattr( other, 'offset' ):
            other = other.offset
        assert isinstance( other, (int,long) ), """Only know how to add integer/long offsets"""
        return VBOOffset( self, other )
    cdef int check_live( self ):
        if self.data is _NULL:
            raise RuntimeError( """Attempting to use a deleted VBO""" )

    __enter__ = bind
    def __exit__( self, exc_type=None, exc_val=None, exc_tb=None ):
        """Context manager exit"""
        self.unbind()
        return False # do not supress exceptions...


cdef class VBOOffset:
    """Offset into a VBO instance

    This is just a convenience object that lets you say
    vbo + integer and have the value passed as the correct
    data-type instead of being interpreted as a pointer to
    an integer-array of the offset.
    """
    cdef public VBO vbo
    cdef public unsigned int offset
    def __cinit__( self, VBO vbo, unsigned int offset ):
        self.vbo = vbo
        Py_XINCREF( vbo )
        self.offset = offset
    def __dealloc__( self ):
        if self.vbo is not None:
            Py_XDECREF( self.vbo )
            self.vbo = None

    def __getattr__( self, key ):
        if key != 'vbo':
            return getattr( self.vbo, key )
        raise AttributeError( 'No %r key in VBOOffset'%(key,))
    def __add__( self, other ):
        if hasattr( other, 'offset' ):
            other = other.offset
        return VBOOffset( self.vbo, self.offset + other )
    cdef int check_live( self ):
        if self.vbo is not None:
            return self.vbo.check_live()
        else:
            raise RuntimeError( """Attempting to use offset into deleted VBO""" )

cdef class VBOHandler(FormatHandler):
    """Handles VBO instances passed in as array data"""
    cdef object vp0
    cdef object arrayType # import and use explicit reference...
    isOutput = False
    def __init__( self ):
        self.vp0 = ctypes.c_void_p( 0 )
        from OpenGL.arrays.arraydatatype import ArrayDatatype
        self.arrayType = ArrayDatatype
    cdef object c_dataPointer( self, object instance ):
        """Retrieve data-pointer directly"""
        (<VBO>instance).check_live()
        return 0
    cdef c_from_param( self, object instance, object typeCode ):
        """simple function-based from_param"""
        (<VBO>instance).check_live()
        return self.vp0
    cdef c_asArray( self, object instance, object typeCode ):
        """Retrieve the given value as a (contiguous) array of type typeCode"""
        (<VBO>instance).check_live()
        return instance
    cdef c_arrayByteCount( self, object instance ):
        """Given a data-value, calculate number of bytes required to represent"""
        (<VBO>instance).check_live()
        return self.arrayType.arrayByteCount( (<VBO>instance).data )
    cdef c_arrayToGLType( self, object instance ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        (<VBO>instance).check_live()
        return self.arrayType.arrayToGLType( (<VBO>instance).data )
    cdef c_arraySize( self, object instance, object typeCode ):
        """Retrieve array size reference"""
        (<VBO>instance).check_live()
        return self.arrayType.arraySize( (<VBO>instance).data )
    cdef c_unitSize( self, object instance, typeCode ):
        """Retrieve last dimension of the array"""
        (<VBO>instance).check_live()
        return self.arrayType.unitSize( (<VBO>instance).data )
    cdef c_dimensions( self, object instance ):
        """Retrieve full set of dimensions for the array as tuple"""
        (<VBO>instance).check_live()
        return self.arrayType.dimensions( (<VBO>instance).data )

cdef class VBOOffsetHandler(FormatHandler):
    cdef object arrayType # import and use explicit reference...
    isOutput = False
    def __init__( self ):
        from OpenGL.arrays.arraydatatype import ArrayDatatype
        self.arrayType = ArrayDatatype

    cdef object c_dataPointer( self, object instance ):
        """Retrieve data-pointer directly"""
        (<VBOOffset>instance).check_live()
        return (<VBOOffset>instance).offset
    cdef c_from_param( self, object instance, object typeCode ):
        """simple function-based from_param"""
        (<VBOOffset>instance).check_live()
        return ctypes.c_void_p( (<VBOOffset>instance).offset )
    cdef c_asArray( self, object instance, object typeCode ):
        """Retrieve the given value as a (contiguous) array of type typeCode"""
        (<VBOOffset>instance).check_live()
        return instance

    cdef c_arrayByteCount( self, object instance ):
        """Given a data-value, calculate number of bytes required to represent"""
        (<VBOOffset>instance).check_live()
        return self.arrayType.arrayByteCount( (<VBOOffset>instance).vbo.data )
    cdef c_arrayToGLType( self, object instance ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        (<VBOOffset>instance).check_live()
        return self.arrayType.arrayToGLType( (<VBOOffset>instance).vbo.data )
    cdef c_arraySize( self, object instance, object typeCode ):
        """Retrieve array size reference"""
        (<VBOOffset>instance).check_live()
        return self.arrayType.arraySize( (<VBOOffset>instance).vbo.data )
    cdef c_unitSize( self, object instance, typeCode ):
        """Retrieve last dimension of the array"""
        (<VBOOffset>instance).check_live()
        return self.arrayType.unitSize( (<VBOOffset>instance).vbo.data )
    cdef c_dimensions( self, object instance ):
        """Retrieve full set of dimensions for the array as tuple"""
        (<VBOOffset>instance).check_live()
        return self.arrayType.dimensions( (<VBOOffset>instance).vbo.data )
