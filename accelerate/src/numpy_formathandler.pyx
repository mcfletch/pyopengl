"""Accelerator for numpy format handler operations"""
#cython: language_level=3
from ctypes import c_void_p
import numpy as np
cimport numpy as np
from OpenGL_accelerate.formathandler cimport FormatHandler
import traceback, weakref
from OpenGL.error import CopyError
from OpenGL._bytes import bytes,unicode

cdef extern from "Python.h":
    cdef void Py_INCREF( object )

cdef extern from "numpy/arrayobject.h":
    cdef np.ndarray PyArray_FromArray( np.ndarray, np.dtype, int )
    cdef np.ndarray PyArray_ContiguousFromAny( object op, int, int, int max_depth)
    cdef int PyArray_Check( object )
    cdef int PyArray_CheckScalar( object )
    int NPY_ARRAY_CARRAY
    int NPY_ARRAY_FORCECAST
    int PyArray_ISCARRAY( np.ndarray instance )
    int PyArray_ISCARRAY_RO( np.ndarray instance )
    cdef np.ndarray PyArray_Zeros(int nd, np.npy_intp* dims, np.dtype, int fortran)
    cdef np.ndarray PyArray_EnsureArray(object)
    cdef int PyArray_FillWithScalar(object, object)
    cdef void import_array()
    cdef void* PyArray_DATA( np.ndarray )
    cdef int PyArray_NDIM( np.ndarray )
    cdef int *PyArray_DIMS( np.ndarray )
    cdef int PyArray_DIM( np.ndarray, int dim )
    cdef np.dtype PyArray_DESCR( np.ndarray )
    cdef np.npy_intp PyArray_SIZE( np.ndarray )

cdef np.dtype array_descr( np.ndarray array ):
    """Wrap PyArray_DESCR and incref to deal with the "borrowed" reference"""
    cdef np.dtype desc = PyArray_DESCR( array )
    Py_INCREF(<object> desc)
    return desc

cdef class NumpyHandler(FormatHandler):
    cdef public dict array_to_gl_constant
    cdef public dict gl_constant_to_array
    isOutput = True
    HANDLED_TYPES = (
        np.ndarray,
        np.bool_,
        np.intc,
        np.uintc,
        np.int8,
        np.uint8,
        np.int16,
        np.uint16,
        np.int32,
        np.uint32,
        np.int64,
        np.uint64,
        np.int64,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        np.complex64,
        np.complex128,
        np.bytes_,
        np.str_,
        np.void,
        np.datetime64,
        np.timedelta64,
    )
    if hasattr(np,'float128'):
        HANDLED_TYPES += (np.float128,)
    if hasattr(np,'complex256'):
        HANDLED_TYPES += (np.complex256,)
    
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
            if array_descr(instance) != targetType:
                raise CopyError(
                    """Array of type %r passed, required array of type %r""",
                    array_descr(instance).char, targetType.char,
                )                    
        if not PyArray_ISCARRAY_RO( instance ):
            raise CopyError(
                """from_param received a non-contiguous array! %s"""%(
                    working,
                )
            )
        return c_void_p(<size_t> PyArray_DATA(working))
    
    cdef c_dataPointer( self, object instance ):
        """Retrieve data-pointer directly"""
        return <size_t> PyArray_DATA(<np.ndarray>self.c_check_array( instance ))
    cdef c_zeros( self, object dims, object typeCode ):
        """Create an array initialized to zeros"""
        cdef np.ndarray c_dims
        try:
            c_dims = PyArray_ContiguousFromAny( 
                [int(x) for x in dims], np.NPY_INTP, 1,1 
            )
        except (ValueError,TypeError) as err:
            dims = (int(dims),)
            c_dims = PyArray_ContiguousFromAny( 
                dims, np.NPY_INTP, 1,1 
            )
        cdef np.dtype typecode = self.typeCodeToDtype( typeCode )
        Py_INCREF( typecode )
        cdef np.npy_intp ndims = PyArray_SIZE(c_dims)
        cdef np.ndarray result = PyArray_Zeros( <int>ndims, <np.npy_intp *>PyArray_DATA(c_dims), typecode, 0 )
        # Py_INCREF( result )
        return result
    cdef c_arraySize( self, object instance, object typeCode ):
        """Retrieve array size reference"""
        return (<np.ndarray>self.c_check_array( instance )).size
    cdef c_arrayByteCount( self, object instance ):
        """Given a data-value, calculate number of bytes required to represent"""
        return instance.nbytes
    cdef c_arrayToGLType( self, object instance ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        cdef np.ndarray value = self.c_check_array( instance )
        cdef object constant = self.array_to_gl_constant.get( array_descr(value) )
        if constant is None:
            raise TypeError(
                """Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
                    array_descr(value), self.array_to_gl_constant.keys(), value,
                )
            )
        return constant
    cdef c_asArray( self, object instance, object typeCode ):
        """Retrieve the given value as a (contiguous) array of type typeCode"""
        cdef np.ndarray working
        cdef np.dtype typecode
        cdef int res
        if PyArray_CheckScalar(instance):
            Py_INCREF(instance)
            working = self.c_zeros((1,), typeCode)
            res = PyArray_FillWithScalar(<object>working, instance)
            if res < -1:
                raise ValueError("Unable to fill new array with value %r (%s)"%(instance,instance.__class__))
        else:
            working = (<np.ndarray>self.c_check_array( instance ))
        if typeCode is None:
            typecode = array_descr(working)
        else:
            typecode = self.typeCodeToDtype( typeCode )
        return self.contiguous( working, typecode )
    cdef c_unitSize( self, object instance, typeCode ):
        """Retrieve last dimension of the array"""
        return PyArray_DIM(instance, PyArray_NDIM(instance)-1)
    cdef c_dimensions( self, object instance ):
        """Retrieve full set of dimensions for the array as tuple"""
        return instance.shape

    cdef np.dtype typeCodeToDtype( self, object typeCode ):
        """Convert type-code specification to a numpy dtype instance"""
        if isinstance( typeCode, np.dtype ):
            return typeCode
        elif isinstance( typeCode, (bytes,unicode) ):
            return np.dtype( typeCode )
        else:
            return self.gl_constant_to_array[ typeCode ]
    cdef np.ndarray contiguous( self, np.ndarray instance, np.dtype dtype ):
        """Ensure that this instance is a contiguous array
        
        :param instance: numpy instance to convert to contiguous array
        :param dtype: numpy dtype to which to convert the array
            IFF self.ERROR_ON_COPY then any required conversions 
            will raise a :class:`CopyError`
        
        :rtype: np.ndarray
        """
        if self.ERROR_ON_COPY:
            if not PyArray_ISCARRAY_RO( instance ):
                raise CopyError(
                    """Non-contiguous array passed""",
                    instance,
                )
            elif array_descr(instance) != dtype:
                raise CopyError(
                    """Array of type %r passed, required array of type %r""",
                    array_descr(instance).char, dtype.char,
                )
            # okay, so just return...
            return instance 
        else:
            # "convert" regardless (will return same instance if already contiguous)
            if PyArray_CheckScalar(instance):
                Py_INCREF( <object> instance )
                return PyArray_EnsureArray(instance)
            if not PyArray_ISCARRAY_RO( instance ) or array_descr(instance) != dtype:
                # TODO: make sure there's no way to segfault here 
                # Py_INCREF( <object> instance )
                Py_INCREF( <object> dtype )
                return PyArray_FromArray( 
                    instance, 
                    dtype, 
                    NPY_ARRAY_CARRAY|NPY_ARRAY_FORCECAST
                )

            else:
                return instance


# Cython numpy tutorial neglects to mention this AFAICS
# get segfaults without it
import_array()
