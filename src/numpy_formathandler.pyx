"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import numpy as np
cimport numpy as np
import traceback, weakref
from OpenGL.error import CopyError
from OpenGL.arrays import formathandler
import OpenGL

cdef extern from "Python.h":
	cdef void Py_INCREF( object )

cdef extern from "numpy/arrayobject.h":
	cdef np.ndarray PyArray_FromArray( np.ndarray, np.dtype, int )
	cdef np.ndarray PyArray_ContiguousFromAny( object op, int, int, int max_depth)
	int NPY_CARRAY
	int NPY_FORCECAST
	int PyArray_ISCARRAY( np.ndarray instance )
	cdef np.ndarray PyArray_Zeros(int nd, np.Py_intptr_t dims, dtype, int fortran)
	cdef void import_array()

cdef class NumpyHandler:
	cdef public int ERROR_ON_COPY
	cdef public dict array_to_gl_constant
	cdef public dict gl_constant_to_array
	isOutput = True
	HANDLED_TYPES = (np.ndarray,)
	
	def __init__( self, ERROR_ON_COPY=None, a_to_gl=None, gl_to_a=None ):
		if ERROR_ON_COPY is None:
			ERROR_ON_COPY = OpenGL.ERROR_ON_COPY
		if a_to_gl is None:
			from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING
			a_to_gl = ARRAY_TO_GL_TYPE_MAPPING
		if gl_to_a is None:
			from OpenGL.arrays.numpymodule import GL_TYPE_TO_ARRAY_MAPPING
			gl_to_a = GL_TYPE_TO_ARRAY_MAPPING
		self.ERROR_ON_COPY = ERROR_ON_COPY
		self.array_to_gl_constant = a_to_gl
		self.gl_constant_to_array = gl_to_a
	def register( self, types=None ):
		"""Register this class as handler for given set of types"""
		formathandler.FormatHandler.TYPE_REGISTRY.register( self, types )
	def registerReturn( self ):
		"""Register this handler as the default return-type handler"""
		formathandler.FormatHandler.TYPE_REGISTRY.registerReturn( self )
		
	def from_param( self, np.ndarray instance, object typeCode = None ):
		"""simple function-based from_param"""
		if PyArray_ISCARRAY( instance ):
			return <long> (instance.data)
		raise CopyError(
			"""from_param received a non-contiguous array! %s"""%(
				instance,
			)
		)
	def dataPointer( self, np.ndarray instance ):
		"""Retrieve data-pointer directly"""
		return <unsigned long> instance.data 
	def zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		cdef np.ndarray c_dims = PyArray_ContiguousFromAny( 
			dims, np.NPY_ULONG, 1,1 
		)
		typecode = self.typeCodeToDtype( typeCode )
		Py_INCREF( typecode )
		return PyArray_Zeros( c_dims.shape[0], <np.Py_intptr_t>c_dims.data, typecode, 0 )
	def arraySize( self, np.ndarray instance, object typeCode=None ):
		"""Retrieve array size reference"""
		return instance.size 
	def arrayByteCount( self, np.ndarray instance, typeCode = None ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return instance.nbytes
	def arrayToGLType( self, np.ndarray value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		cdef object constant = self.array_to_gl_constant.get( value.dtype )
		if constant is None:
			raise TypeError(
				"""Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
					value.dtype, self.array_to_gl_constant.keys(), value,
				)
			)
		return constant
	def asArray( self, np.ndarray instance, object typeCode = None ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		cdef np.dtype typecode
		try:
			typecode = self.typeCodeToDtype( typeCode )
		except KeyError, err:
			typecode = instance.dtype
		return self.contiguous( instance, typecode )
	def unitSize( self, np.ndarray instance, typeCode=None ):
		"""Retrieve last dimension of the array"""
		return instance.shape[instance.ndim-1]
	def dimensions( self, object instance, typeCode=None ):
		"""Retrieve full set of dimensions for the array as tuple"""
		return instance.shape

	cdef np.dtype typeCodeToDtype( self, object typeCode=None ):
		"""Convert type-code specification to a numpy dtype instance"""
		if isinstance( typeCode, np.dtype ):
			return typeCode
		elif isinstance( typeCode, str ):
			return np.dtype( typeCode )
		else:
			return self.gl_constant_to_array[ typeCode ]
	cdef contiguous( self, np.ndarray instance, np.dtype dtype ):
		"""Ensure that this instance is a contiguous array"""
		if self.ERROR_ON_COPY:
			if not PyArray_ISCARRAY( instance ):
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
			# "convert" regardless (will return same instance if already contiguous)
			Py_INCREF( <object> dtype )
			return PyArray_FromArray( 
				instance, dtype, NPY_CARRAY|NPY_FORCECAST
			)

# Cython numpy tutorial neglects to mention this AFAICS
# get segfaults without it
import_array()
