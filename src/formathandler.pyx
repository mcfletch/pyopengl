cdef class FormatHandler:
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
		raise NotImplemented( """%s does not define from_param method"""%(self,))
	def dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		return self.c_dataPointer( instance )
	cdef object c_dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		raise NotImplemented( """%s does not define dataPointer method"""%(self,))
	def zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		return self.c_zeros( dims, typeCode )
	cdef c_zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		raise NotImplemented( """%s does not define zeros method"""%(self,))
	def arraySize( self, object instance, object typeCode=None ):
		"""Retrieve array size reference"""
		return self.c_arraySize( instance, typeCode )
	cdef c_arraySize( self, object instance, object typeCode ):
		"""Retrieve array size reference"""
		raise NotImplemented( """%s does not define arraySize method"""%(self,))
	def arrayByteCount( self, object instance, typeCode = None ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return self.c_arrayByteCount( instance, typeCode )
	cdef c_arrayByteCount( self, object instance, typeCode ):
		"""Given a data-value, calculate number of bytes required to represent"""
		raise NotImplemented( """%s does not define arrayByteCount method"""%(self,))
	def arrayToGLType( self, object value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		return self.c_arrayToGLType( value )
	cdef c_arrayToGLType( self, object value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		raise NotImplemented( """%s does not define arrayToGLType method"""%(self,))
	def asArray( self, object instance, object typeCode = None ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		return self.c_asArray( instance, typeCode )
	cdef c_asArray( self, object instance, object typeCode ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		raise NotImplemented( """%s does not define asArray method"""%(self,))
	def unitSize( self, object instance, typeCode=None ):
		"""Retrieve last dimension of the array"""
		return self.c_unitSize( instance, typeCode )
	cdef c_unitSize( self, object instance, typeCode ):
		"""Retrieve last dimension of the array"""
		raise NotImplemented( """%s does not define unitSize method"""%(self,))
	def dimensions( self, object instance, typeCode=None ):
		"""Retrieve full set of dimensions for the array as tuple"""
		return self.c_dimensions( instance, typeCode )
	cdef c_dimensions( self, object instance, typeCode ):
		"""Retrieve full set of dimensions for the array as tuple"""
		raise NotImplemented( """%s does not define dimensions method"""%(self,))
