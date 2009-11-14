"""VertexBufferObject helper class"""
from OpenGL import GL
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL.arrays.formathandler import FormatHandler
from OpenGL.GL.ARB import vertex_buffer_object
from OpenGL import constants, error
import ctypes,logging
log = logging.getLogger( 'OpenGL.arrays.vbo' )


import weakref
__all__ = ('VBO','VBOHandler','mapVBO')

class Implementation( object ):
    """Abstraction point for the various implementations that can be used
    """
    available = False
    def _arbname( self, name ):
        return (
            (name.startswith( 'gl' ) and name.endswith( 'ARB' )) or 
            (name.startswith( 'GL_' ) and name.endswith( 'ARB' ))
        ) and (name != 'glInitVertexBufferObjectARB')
    def basename( self, name ):
        if name.endswith( '_ARB' ):
            return name[:-4]
        elif name.endswith( 'ARB' ):
            return name[:-3]
        else:
            return name
    def __init__( self ):
        names = [name for name in dir(vertex_buffer_object) if self._arbname( name )]
        if not GL.glBufferData:
            for name in names:
                setattr( self, self.basename(name), getattr( vertex_buffer_object, name ))
            self.available = True
        elif vertex_buffer_object.glBufferDataARB:
            for name in names:
                setattr( self, self.basename(name), getattr( GL, self.basename(name) ))
            self.available = True
    def __nonzero__( self ):
        return self.available
    def deleter( self, buffers, key):
        """Produce a deleter callback to delete the given buffer"""
        nfe = error.NullFunctionError
        gluint = constants.GLuint
        def doBufferDeletion( *args, **named ):
            while buffers:
                try:
                    buffer = buffers.pop()
                except IndexError, err:
                    break
                else:
                    try:
                        # Note that to avoid ERROR_ON_COPY issues 
                        # we have to pass an array-compatible type here...
                        buf = gluint( buffer )
                        self.glDeleteBuffers(1, buf)
                    except (AttributeError, nfe), err:
                        pass
            try:
                self._DELETERS_.pop( key )
            except KeyError, err:
                pass
        return doBufferDeletion
    _DELETERS_ = {}

IMPLEMENTATION = None

def get_implementation( *args ):
    """Retrieve the appropriate implementation for this machine"""
    global IMPLEMENTATION
    if IMPLEMENTATION is None:
        IMPLEMENTATION = Implementation()
    return IMPLEMENTATION

from OpenGL import acceleratesupport
VBO = None
if acceleratesupport.ACCELERATE_AVAILABLE:
    try:
        from OpenGL_accelerate.vbo import (
            VBO,VBOOffset,VBOHandler,VBOOffsetHandler,
        )
    except ImportError, err:
        log.warn(
            "Unable to load VBO accelerator from OpenGL_accelerate"
        )
if VBO is None:
    class VBO( object ):
        """Instances can be passed into array-handling routines
        
        You can check for whether VBOs are supported by accessing the implementation
        attribute of the VBO, which will raise a RuntimeError if there is no available 
        implementation.
        """
        copied = False
        _no_cache_ = True # do not cache in context data arrays
        def __init__( 
            self, data, usage='GL_DYNAMIC_DRAW', 
            target='GL_ARRAY_BUFFER', size=None,
        ):
            self.usage = usage 
            self.set_array( data, size )
            self.target = target 
            self.buffers = []
            self._copy_segments = []
        _I_ = None
        implementation = property( get_implementation, )
        def resolve( self, value ):
            """Resolve string constant to constant"""
            if isinstance( value, (str,unicode)):
                return getattr( self.implementation, self.implementation.basename( value ) )
            return value
        def set_array( self, data, size=None ):
            """Update our entire array with new data"""
            self.data = data 
            self.copied = False
            if size is not None:
                self.size = size
            elif self.data is not None:
                self.size = ArrayDatatype.arrayByteCount( self.data )
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
            data = ArrayDatatype.asArray( array )
            start = (slice.start or 0) 
            stop = (slice.stop or len(self.data))
            if start < 0:
                start += len(self.data)
                start = max((start,0))
            if stop < 0:
                stop += len(self.data)
                stop = max((stop,0))
            self.data[ slice ] = data
            if self.copied and self.buffers:
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
                    size = ArrayDatatype.arrayByteCount( data ) / len(array)
                    #baseSize = ArrayDatatype.unitSize( data )
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
            if key not in ('data','usage','target','buffers', 'copied','_I_','implementation','_copy_segments' ):
                return getattr( self.data, key )
            else:
                raise AttributeError( key )
        def create_buffers( self ):
            """Create the internal buffer(s)"""
            assert not self.buffers, """Already created the buffer"""
            self.buffers = [ long(self.implementation.glGenBuffers(1)) ]
            self.target = self.resolve( self.target )
            self.usage = self.resolve( self.usage )
            self.implementation._DELETERS_[ id(self) ] = weakref.ref( self, self.implementation.deleter( self.buffers, id(self) ))
            return self.buffers
        def copy_data( self ):
            """Copy our data into the buffer on the GL side"""
            assert self.buffers, """Should do create_buffers before copy_data"""
            if self.copied:
                if self._copy_segments:
                    while self._copy_segments:
                        start,size,data  = self._copy_segments.pop(0)
                        dataptr = ArrayDatatype.voidDataPointer( data )
                        self.implementation.glBufferSubData(self.target, start, size, dataptr)
            else:
                if self.data is not None and self.size is None:
                    self.size = ArrayDatatype.arrayByteCount( self.data )
                self.implementation.glBufferData(
                    self.target, 
                    self.size,
                    self.data,
                    self.usage,
                )
                self.copied = True
        def delete( self ):
            """Delete this buffer explicitly"""
            if self.buffers:
                while self.buffers:
                    try:
                        self.implementation.glDeleteBuffers(1, self.buffers.pop(0))
                    except (AttributeError,error.NullFunctionError), err:
                        pass
        def bind( self ):
            """Bind this buffer for use in vertex calls"""
            if not self.buffers:
                buffers = self.create_buffers()
            self.implementation.glBindBuffer( self.target, self.buffers[0])
            self.copy_data()
        def unbind( self ):
            """Unbind the buffer (make normal array operations active)"""
            self.implementation.glBindBuffer( self.target,0 )
        
        def __add__( self, other ):
            """Add an integer to this VBO (offset)"""
            if hasattr( other, 'offset' ):
                other = other.offset 
            assert isinstance( other, (int,long) ), """Only know how to add integer/long offsets"""
            return VBOOffset( self, other )
        
        __enter__ = bind
        def __exit__( self, exc_type=None, exc_val=None, exc_tb=None ):
            """Context manager exit"""
            self.unbind()
            return False # do not supress exceptions...

    class VBOOffset( object ):
        def __init__( self, vbo, offset ):
            self.vbo = vbo 
            self.offset = offset 
        def __getattr__( self, key ):
            if key != 'vbo':
                return getattr( self.vbo, key )
            raise AttributeError( 'No %r key in VBOOffset'%(key,))
        def __add__( self, other ):
            if hasattr( other, 'offset' ):
                other = other.offset 
            return VBOOffset( self.vbo, self.offset + other )


    class VBOHandler( FormatHandler ):
        """Handles VBO instances passed in as array data"""
        vp0 = ctypes.c_void_p( 0 )
        def dataPointer( self, instance ):
            """Retrieve data-pointer from the instance's data
            
            Is always NULL, to indicate use of the bound pointer
            """
            return 0
        def from_param( self, instance, typeCode=None ):
            return self.vp0
        def zeros( self, dims, typeCode ):
            """Not implemented"""
            raise NotImplemented( """Don't have VBO output support yet""" )
        ones = zeros 
        def asArray( self, value, typeCode=None ):
            """Given a value, convert to array representation"""
            return value
        def arrayToGLType( self, value ):
            """Given a value, guess OpenGL type of the corresponding pointer"""
            return ArrayDatatype.arrayToGLType( value.data )
        def arrayByteCount( self, value ):
            return ArrayDatatype.arrayByteCount( value.data )
        def arraySize( self, value, typeCode = None ):
            """Given a data-value, calculate dimensions for the array"""
            return ArrayDatatype.arraySize( value.data )
        def unitSize( self, value, typeCode=None ):
            """Determine unit size of an array (if possible)"""
            return ArrayDatatype.unitSize( value.data )
        def dimensions( self, value, typeCode=None ):
            """Determine dimensions of the passed array value (if possible)"""
            return ArrayDatatype.dimensions( value.data )

    class VBOOffsetHandler( VBOHandler ):
        def dataPointer( self, instance ):
            """Retrieve data-pointer from the instance's data
            
            Is always NULL, to indicate use of the bound pointer
            """
            return instance.offset
        def from_param( self, instance, typeCode=None ):
            return ctypes.c_void_p( instance.offset )



FormatHandler.loadAll() # otherwise just the VBO would get loaded :)
VBO_HANDLER = VBOHandler()
VBO_HANDLER.register( [ VBO ] )

VBOOFFSET_HANDLER = VBOOffsetHandler()
VBOOFFSET_HANDLER.register( [ VBOOffset ] )

PyBuffer_FromMemory = ctypes.pythonapi.PyBuffer_FromMemory
PyBuffer_FromMemory.restype = ctypes.py_object
_cleaners = {}
def _cleaner( vbo ):
    def clean( ref ):
        try:
            _cleaners.pop( vbo )
        except Exception, err:
            pass
        else:
            glUnmapBuffer( vbo.target )
    return clean

def mapVBO( vbo, access=GL.GL_READ_WRITE ):
    """Map the given buffer into a numpy array...
    
    Method taken from:
     http://www.mail-archive.com/numpy-discussion@lists.sourceforge.net/msg01161.html
     
    This should be considered an *experimental* API,
    it is not guaranteed to be available in future revisions 
    of this library!
    """
    vp = glMapBuffer( vbo.target, access )
    buffer = PyBuffer_FromMemory( 
        ctypes.c_void_p(vp), vbo.size 
    )
    array = frombuffer( buffer, 'B' )
    _cleaners[vbo] = weakref.ref( array, _cleaner( vbo ))
    return array
