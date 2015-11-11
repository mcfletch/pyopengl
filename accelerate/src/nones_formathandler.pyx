"""Accelerator for None-as-an-array format handler operations"""
from OpenGL_accelerate.formathandler cimport FormatHandler

cdef class NoneHandler(FormatHandler):
	isOutput = False
	HANDLED_TYPES = (type(None),)
	
	cdef c_from_param( self, object instance, object typeCode ):
		"""simple function-based from_param"""
		return None
	cdef c_dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		return None
	cdef c_arraySize( self, object instance, object typeCode ):
		"""Retrieve array size reference"""
		return 0
	cdef c_arrayByteCount( self, object instance ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return 0
	cdef c_asArray( self, object instance, object typeCode ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		return None
	cdef c_dimensions( self, object instance ):
		"""Retrieve full set of dimensions for the array as tuple"""
		return (0,)
