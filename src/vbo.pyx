"""Cython-coded VBO implementation"""
import ctypes, weakref
from OpenGL.arrays import formathandler

class _Holder:
	pass

cdef class VBO:
	"""Instances can be passed into array-handling routines
	
	You can check for whether VBOs are supported by accessing the implementation
	attribute of the VBO, which will raise a RuntimeError if there is no available 
	implementation.
	"""
	cdef public int copied
	cdef public int created
	cdef public unsigned int buffer 
	cdef public object data 
	cdef public object target
	cdef public object usage
	cdef public int resolved 
	cdef public object balast 
	cdef public object target_spec
	cdef public object usage_spec
	cdef public list _copy_segments
	cdef public object _I_
	cdef public object arrayType
	_no_cache_ = True # do not cache in context data arrays
	
	def __init__( 
		self, data, usage='GL_DYNAMIC_DRAW', 
		target='GL_ARRAY_BUFFER',
	):
		self.data = data 
		self.resolved = self.created = self.copied = False 
		self.usage_spec = usage 
		self.target_spec = target 
		self.balast = _Holder()
		self._copy_segments = []
		self._I_ = None
		from OpenGL.arrays.arraydatatype import ArrayDatatype
		self.arrayType = ArrayDatatype
	@property 
	def implementation( self ):
		"""Retrieve our implementation reference"""
		return self.get_implementation()
	cdef get_implementation( self ):
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
	def set_array( self, data ):
		"""Update our entire array with new data"""
		self.data = data 
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
			self.balast, 
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
				self.data,
				self.usage,
			)
			self.copied = True
	def delete( self ):
		"""Delete this buffer explicitly"""
		if self.created:
			self.created = False
			try:
				self.get_implementation().glDeleteBuffers(1, [self.buffer])
			except AttributeError, err:
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
	

cdef class VBOOffset:
	cdef public VBO vbo 
	cdef public unsigned int offset
	def __init__( self, VBO vbo, unsigned int offset ):
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

cdef class VBOHandler:
	"""Handles VBO instances passed in as array data"""
	cdef object vp0 
	cdef object arrayType # import and use explicit reference...
	isOutput = False
	def __init__( self ):
		self.vp0 = ctypes.c_void_p( 0 )
		from OpenGL.arrays.arraydatatype import ArrayDatatype
		self.arrayType = ArrayDatatype
	def dataPointer( self, VBO instance ):
		"""Retrieve data-pointer from the instance's data
		
		Is always NULL, to indicate use of the bound pointer
		"""
		return 0
	def from_param( self, VBO instance, object typeCode=None ):
		return self.vp0
	def zeros( self, dims, typeCode ):
		"""Not implemented"""
		raise NotImplemented( """Don't have VBO output support yet""" )
	ones = zeros 
	def asArray( self, VBO value, typeCode=None ):
		"""Given a value, convert to array representation"""
		return value
	def arrayToGLType( self, value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		return self.arrayType.arrayToGLType( value.data )
	def arraySize( self, value, typeCode = None ):
		"""Given a data-value, calculate dimensions for the array"""
		return self.arrayType.arraySize( value.data )
	def unitSize( self, value, typeCode=None ):
		"""Determine unit size of an array (if possible)"""
		return self.arrayType.unitSize( value.data )
	def dimensions( self, value, typeCode=None ):
		"""Determine dimensions of the passed array value (if possible)"""
		return self.arrayType.dimensions( value.data )
	def register( self, types=None ):
		"""Register this class as handler for given set of types"""
		formathandler.FormatHandler.TYPE_REGISTRY.register( self, types )
	def registerReturn( self ):
		"""Register this handler as the default return-type handler"""
		formathandler.FormatHandler.TYPE_REGISTRY.registerReturn( self )

cdef class VBOOffsetHandler:
	cdef object arrayType # import and use explicit reference...
	isOutput = False
	def __init__( self ):
		from OpenGL.arrays.arraydatatype import ArrayDatatype
		self.arrayType = ArrayDatatype
	def dataPointer( self, VBOOffset instance ):
		"""Retrieve data-pointer from the instance's data
		
		Is always NULL, to indicate use of the bound pointer
		"""
		return instance.offset
	def from_param( self, VBOOffset instance, object typeCode=None ):
		return ctypes.c_void_p( instance.offset )
	def zeros( self, dims, typeCode ):
		"""Not implemented"""
		raise NotImplemented( """Don't have VBO output support yet""" )
	ones = zeros 
	def asArray( self, VBOOffset value, typeCode=None ):
		"""Given a value, convert to array representation"""
		return value
	def arrayToGLType( self, VBOOffset value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		return self.arrayType.arrayToGLType( value.vbo.data )
	def arraySize( self, VBOOffset value, typeCode = None ):
		"""Given a data-value, calculate dimensions for the array"""
		return self.arrayType.arraySize( value.vbo.data )
	def unitSize( self, VBOOffset value, typeCode=None ):
		"""Determine unit size of an array (if possible)"""
		return self.arrayType.unitSize( value.vbo.data )
	def dimensions( self, value, typeCode=None ):
		"""Determine dimensions of the passed array value (if possible)"""
		return self.arrayType.dimensions( value.vbo.data )
	def register( self, types=None ):
		"""Register this class as handler for given set of types"""
		formathandler.FormatHandler.TYPE_REGISTRY.register( self, types )
	def registerReturn( self ):
		"""Register this handler as the default return-type handler"""
		formathandler.FormatHandler.TYPE_REGISTRY.registerReturn( self )
