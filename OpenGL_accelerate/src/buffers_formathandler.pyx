"""Cython memoryview implementation of buffer-api format handler"""
from ctypes import c_void_p
from OpenGL_accelerate.formathandler cimport FormatHandler
import traceback, weakref
from OpenGL.error import CopyError
from OpenGL._bytes import bytes,unicode

# Following is from the old python_buffer.pxd
cdef extern from "Python.h":

    cdef enum:
        PyBUF_SIMPLE,
        PyBUF_WRITABLE,
        PyBUF_WRITEABLE, # backwards compatability
        PyBUF_FORMAT,
        PyBUF_ND,
        PyBUF_STRIDES,
        PyBUF_C_CONTIGUOUS,
        PyBUF_F_CONTIGUOUS,
        PyBUF_ANY_CONTIGUOUS,
        PyBUF_INDIRECT,
        PyBUF_CONTIG,
        PyBUF_CONTIG_RO,
        PyBUF_STRIDED,
        PyBUF_STRIDED_RO,
        PyBUF_RECORDS,
        PyBUF_RECORDS_RO,
        PyBUF_FULL,
        PyBUF_FULL_RO,
        PyBUF_READ,
        PyBUF_WRITE,
        PyBUF_SHADOW

    bint PyObject_CheckBuffer(object obj)

    int PyObject_GetBuffer(object obj, Py_buffer *view, int flags) except -1
    void PyBuffer_Release(object obj, object view)
    void* PyBuffer_GetPointer(Py_buffer *view, Py_ssize_t *indices)
    int PyObject_CopyToObject(object obj, void *buf, Py_ssize_t len, char fortran) except -1
    bint PyBuffer_IsContiguous(Py_buffer *view, char fort)
    
    object PyMemoryView_FromObject(object obj)
    object PyMemoryView_FromBuffer(Py_buffer *view)

    object PyMemoryView_GetContiguous(object obj, int buffertype, char order)
    
    bint PyMemoryView_Check(object obj)
    Py_buffer *PyMemoryView_GET_BUFFER(object obj)


cdef class MemoryviewHandler(FormatHandler):
    cdef public dict array_to_gl_constant
    cdef public dict gl_constant_to_array
    isOutput = True
    
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

    cdef object c_as_memoryview( self, object instance ):
        """Ensure instance is a memory view instance or make it one"""
        if not PyMemoryView_Check( instance ):
            # TODO: respect no-copy flag!
            instance = PyMemoryView_GetContiguous( 
                instance, 
                PyBUF_STRIDES|PyBUF_FORMAT|PyBUF_C_CONTIGUOUS,
                'C'
            )
        return instance
    cdef c_from_param( self, object instance, object typeCode ):
        """simple function-based from_param"""
        if not PyMemoryView_Check( instance ):
            raise TypeError( '''Need a MemoryView instance in from_param (call asArray first)''' )
        return c_void_p( self.c_dataPointer( instance ) )
    cdef c_dataPointer( self, object instance ):
        """Retrieve data-pointer directly"""
        return <size_t> PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance )).buf
    cdef c_zeros( self, object dims, object typeCode ):
        """Create an array initialized to zeros"""
        raise NotImplementedError( "Need to use a subclass to get zeros support" )
    cdef c_arraySize( self, object instance, object typeCode ):
        """Retrieve array size reference"""
        cdef Py_buffer * buffer
        buffer = PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance ) )
        return buffer.len//buffer.itemsize
    cdef c_arrayByteCount( self, object instance ):
        """Given a data-value, calculate number of bytes required to represent"""
        return PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance ) ).len
        
    cdef c_arrayToGLType( self, object instance ):
        """Given a value, guess OpenGL type of the corresponding pointer"""
        cdef Py_buffer * buffer
        buffer = PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance ) )
        cdef object constant = self.array_to_gl_constant.get( buffer.format )
        if constant is None:
            raise TypeError(
                """Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
                    buffer.format, self.array_to_gl_constant.keys(), buffer.format,
                )
            )
        return constant
        
    cdef c_asArray( self, object instance, object typeCode ):
        """Retrieve the given value as a (contiguous) array of type typeCode"""
        return self.c_as_memoryview( instance )
#        cdef Py_buffer * buffer
#        cdef object result
#        result = self.c_as_memoryview( instance )
#        buffer = PyMemoryView_GET_BUFFER( result )
#        actual_type = self.array_to_gl_constant.get( buffer.format, self.array_to_gl_constant )
#        if actual_type != typeCode:
#            raise TypeError( 'Incompatible type: %s, needed %s', buffer.format, typeCode )
#        return result
    cdef c_unitSize( self, object instance, typeCode ):
        """Retrieve last dimension of the array"""
        return PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance ) ).itemsize
    cdef c_dimensions( self, object instance ):
        """Retrieve full set of dimensions for the array as tuple"""
        cdef Py_buffer * buffer
        buffer = PyMemoryView_GET_BUFFER( self.c_as_memoryview( instance ) )
        cdef dim = 0
        cdef list result
        result = []
        for dim in range(buffer.ndim):
            result.append( buffer.shape[dim] )
        return result
