"""Cython-coded base FormatHandler implementation"""

cdef class FormatHandler:
	"""PyOpenGL "Format" plugin implementation
	
	PyOpenGL 3.x allows for multiple Formats for data arrays,
	a FormatHandler provides generic API entry points which 
	allow PyOpenGL to manipulate/interact with data arrays
	in the given format.
	
	This is the C-level accelerator module which allows
	for much faster access to the accelerator by the C-level
	wrapper classes.  This FormatHandler type should only 
	be used as a base class by those FormatHandlers which 
	provide C-level API entry points, you should *not*
	sub-class it in Python.
	"""	
	isOutput = False
	HANDLED_TYPES = ()
	
	def __init__( self):
		"""Initialize the format handler"""
	def register( self, types=None ):
		"""Register this class as handler for given set of types"""
		from OpenGL.arrays.arraydatatype import ArrayDatatype
		ArrayDatatype.getRegistry().register( self, types )
	def registerReturn( self ):
		"""Register this handler as the default return-type handler"""
		from OpenGL.arrays.arraydatatype import ArrayDatatype
		ArrayDatatype.getRegistry().registerReturn( self )
	def registerEquivalent( self, typ, base ):
		"""Register a sub-class for handling as the base-type"""
		
	def from_param( self, object instance, object typeCode = None ):
		"""simple function-based from_param"""
		return self.c_from_param( instance, typeCode )
	cdef object c_from_param( self, object instance, object typeCode ):
		"""C-API for from_param"""
		raise NotImplementedError( """%s does not define from_param method"""%(self,))
	def dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		return self.c_dataPointer( instance )
	cdef object c_dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		raise NotImplementedError( """%s does not define dataPointer method"""%(self,))
	def zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		return self.c_zeros( dims, typeCode )
	cdef c_zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		raise NotImplementedError( """%s does not define zeros method"""%(self,))
	def arraySize( self, object instance, object typeCode=None ):
		"""Retrieve array size reference"""
		return self.c_arraySize( instance, typeCode )
	cdef c_arraySize( self, object instance, object typeCode ):
		"""Retrieve array size reference"""
		raise NotImplementedError( """%s does not define arraySize method"""%(self,))
	def arrayByteCount( self, object instance ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return self.c_arrayByteCount( instance )
	cdef c_arrayByteCount( self, object instance ):
		"""Given a data-value, calculate number of bytes required to represent"""
		raise NotImplementedError( """%s does not define arrayByteCount method"""%(self,))
	def arrayToGLType( self, object value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		return self.c_arrayToGLType( value )
	cdef c_arrayToGLType( self, object value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		raise NotImplementedError( """%s does not define arrayToGLType method"""%(self,))
	def asArray( self, object instance, object typeCode = None ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		return self.c_asArray( instance, typeCode )
	cdef c_asArray( self, object instance, object typeCode ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		raise NotImplementedError( """%s does not define asArray method"""%(self,))
	def unitSize( self, object instance, typeCode=None ):
		"""Retrieve last dimension of the array"""
		return self.c_unitSize( instance, typeCode )
	cdef c_unitSize( self, object instance, typeCode ):
		"""Retrieve last dimension of the array"""
		raise NotImplementedError( """%s does not define unitSize method"""%(self,))
	def dimensions( self, object instance ):
		"""Retrieve full set of dimensions for the array as tuple"""
		return self.c_dimensions( instance )
	cdef c_dimensions( self, object instance ):
		"""Retrieve full set of dimensions for the array as tuple"""
		raise NotImplementedError( """%s does not define dimensions method"""%(self,))
