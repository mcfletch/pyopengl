"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import numpy as np
cimport numpy as np
import traceback, weakref
from OpenGL.error import CopyError
cdef extern from "numpy/arrayobject.h":
	cdef np.ndarray PyArray_FromArray( np.ndarray, np.dtype, int )
	int NPY_CARRAY
	int NPY_CONTIGUOUS
	int NPY_C_CONTIGUOUS
#	int PyArray_CHKFLAGS( np.ndarray instance, int flags )
	int PyArray_ISCARRAY( np.ndarray instance )
	cdef void import_array()

cdef char* dataPointerC( np.ndarray value ):
	"""Retrieve data-pointer from the ndarray"""
	cdef char* p
	p = value.data
	return p

cdef class NumpyHandler:
	cdef int ERROR_ON_COPY
	def __init__( self, ERROR_ON_COPY=False ):
		self.ERROR_ON_COPY = ERROR_ON_COPY

	def from_param( self, np.ndarray instance ):
		"""simple function-based from_param"""
		pointer = long(<long> dataPointerC( instance ))
		return c_void_p(  pointer )
	def dataPointer( self, np.ndarray instance ):
		"""Retrieve data-pointer directly"""
		return <unsigned long> instance.data 
	def zeros( self, tuple dims, object typeCode ):
		"""Create an array initialized to zeros"""
		return np.zeros( dims, dtype = typeCode )
	def arraySize( self, np.ndarray instance, object typeCode=None ):
		"""Retrieve array size reference"""
		return instance.size 
	def arrayByteCount( self, np.ndarray instance, typeCode = None ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return instance.nbytes
	
	def asArray( self, np.ndarray instance, object typeCode = None ):
		cdef np.dtype typecode
		if typeCode is None:
			typecode = instance.dtype 
		else:
			typecode = np.dtype( typeCode )
		return self.contiguous( instance, typecode )

	cdef contiguous( self, np.ndarray instance, np.dtype dtype ):
		"""Ensure that this instance is a contiguous array"""
		if self.ERROR_ON_COPY:
			if not np.PyArray_CHKFLAGS( instance, NPY_CARRAY ):
				raise CopyError(
					"""Non-contiguous array passed""",
					instance,
				)
			elif instance.dtype != dtype:
				raise CopyError(
					"""Array of type %r passed, required array of type %r""",
					instance.dtype.char, dtype.char,
				)
			# okay, so just return...
			return instance 
		else:
			# just convert regardless...
			return PyArray_FromArray( 
				instance, dtype, NPY_CARRAY
			)

import_array()
