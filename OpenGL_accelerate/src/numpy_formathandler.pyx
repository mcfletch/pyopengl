"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import numpy as np
cimport numpy as np
from OpenGL_accelerate.formathandler cimport FormatHandler
import traceback, weakref
from OpenGL.error import CopyError

cdef extern from "Python.h":
	cdef void Py_INCREF( object )

cdef extern from "numpy/arrayobject.h":
	cdef np.ndarray PyArray_FromArray( np.ndarray, np.dtype, int )
	cdef np.ndarray PyArray_ContiguousFromAny( object op, int, int, int max_depth)
	cdef int PyArray_Check( object )
	int NPY_CARRAY
	int NPY_FORCECAST
	int PyArray_ISCARRAY( np.ndarray instance )
	cdef np.ndarray PyArray_Zeros(int nd, np.Py_intptr_t* dims, np.dtype, int fortran)
	cdef void import_array()

cdef class NumpyHandler(FormatHandler):
	cdef public dict array_to_gl_constant
	cdef public dict gl_constant_to_array
	isOutput = True
	HANDLED_TYPES = (np.ndarray,)
	
	def __init__( self, ERROR_ON_COPY=None, a_to_gl=None, gl_to_a=None ):
		if ERROR_ON_COPY is None:
			from OpenGL import _configflags
			ERROR_ON_COPY = _configflags.ERROR_ON_COPY
		if a_to_gl is None:
			from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING
			a_to_gl = ARRAY_TO_GL_TYPE_MAPPING
		if gl_to_a is None:
			from OpenGL.arrays.numpymodule import GL_TYPE_TO_ARRAY_MAPPING
			gl_to_a = GL_TYPE_TO_ARRAY_MAPPING
		self.ERROR_ON_COPY = ERROR_ON_COPY
		self.array_to_gl_constant = a_to_gl
		self.gl_constant_to_array = gl_to_a
	
	cdef np.ndarray c_check_array( self, object instance ):
		if not PyArray_Check( instance ):
			raise TypeError(
				"""Numpy format handler passed a non-numpy-array object %s (of type %s)"""%( instance, type(instance) ),
			)
		return <np.ndarray> instance
		
	cdef c_from_param( self, object instance, object typeCode ):
		"""simple function-based from_param"""
		cdef np.ndarray working = self.c_check_array( instance )
		cdef np.dtype targetType
		if typeCode:
			targetType = <np.dtype>(self.gl_constant_to_array[ typeCode ])
			if instance.dtype != targetType:
				raise CopyError(
					"""Array of type %r passed, required array of type %r""",
					instance.dtype.char, targetType.char,
				)					
		if not PyArray_ISCARRAY( instance ):
			raise CopyError(
				"""from_param received a non-contiguous array! %s"""%(
					working,
				)
			)
		return c_void_p(<size_t> (working.data))
	
	cdef c_dataPointer( self, object instance ):
		"""Retrieve data-pointer directly"""
		return <size_t> (<np.ndarray>self.c_check_array( instance )).data 
	cdef c_zeros( self, object dims, object typeCode ):
		"""Create an array initialized to zeros"""
		cdef np.ndarray c_dims
		try:
			c_dims = PyArray_ContiguousFromAny( 
				dims, np.NPY_INTP, 1,1 
			)
		except (ValueError,TypeError), err:
			dims = (int(dims),)
			c_dims = PyArray_ContiguousFromAny( 
				dims, np.NPY_INTP, 1,1 
			)
		cdef np.dtype typecode = self.typeCodeToDtype( typeCode )
		Py_INCREF( typecode )
		return PyArray_Zeros( c_dims.shape[0], <np.npy_intp *>c_dims.data, typecode, 0 )
	cdef c_arraySize( self, object instance, object typeCode ):
		"""Retrieve array size reference"""
		return (<np.ndarray>self.c_check_array( instance )).size
	cdef c_arrayByteCount( self, object instance ):
		"""Given a data-value, calculate number of bytes required to represent"""
		return instance.nbytes
	cdef c_arrayToGLType( self, object instance ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		cdef np.ndarray value = self.c_check_array( instance )
		cdef object constant = self.array_to_gl_constant.get( value.dtype )
		if constant is None:
			raise TypeError(
				"""Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
					value.dtype, self.array_to_gl_constant.keys(), value,
				)
			)
		return constant
	cdef c_asArray( self, object instance, object typeCode ):
		"""Retrieve the given value as a (contiguous) array of type typeCode"""
		cdef np.ndarray working = (<np.ndarray>self.c_check_array( instance ))
		cdef np.dtype typecode
		if typeCode is None:
			typecode = working.dtype 
		else:
			typecode = self.typeCodeToDtype( typeCode )
		return self.contiguous( working, typecode )
	cdef c_unitSize( self, object instance, typeCode ):
		"""Retrieve last dimension of the array"""
		return instance.shape[instance.ndim-1]
	cdef c_dimensions( self, object instance ):
		"""Retrieve full set of dimensions for the array as tuple"""
		return instance.shape

	cdef np.dtype typeCodeToDtype( self, object typeCode ):
		"""Convert type-code specification to a numpy dtype instance"""
		if isinstance( typeCode, np.dtype ):
			return typeCode
		elif isinstance( typeCode, str ):
			return np.dtype( typeCode )
		else:
			return self.gl_constant_to_array[ typeCode ]
	cdef np.ndarray contiguous( self, np.ndarray instance, np.dtype dtype ):
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
			if not PyArray_ISCARRAY( instance ) or instance.dtype != dtype:
				# TODO: make sure there's no way to segfault here 
				Py_INCREF( <object> dtype )
				return PyArray_FromArray( 
					instance, dtype, NPY_CARRAY|NPY_FORCECAST
				)
			else:
				return instance

# Cython numpy tutorial neglects to mention this AFAICS
# get segfaults without it
import_array()
