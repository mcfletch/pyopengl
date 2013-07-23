#! /usr/bin/env python
"""Python 3.x buffer-handling (currently just for bytes/bytearray types)
"""
import ctypes,sys
_fields_ = [
    ('buf',ctypes.c_void_p),
    ('obj',ctypes.c_void_p),
    ('len',ctypes.c_size_t),
    ('itemsize',ctypes.c_size_t),

    ('readonly',ctypes.c_int),
    ('ndim',ctypes.c_int),
    ('format',ctypes.c_char_p),
    ('shape',ctypes.POINTER(ctypes.c_size_t)),
    ('strides',ctypes.POINTER(ctypes.c_size_t)),
    ('suboffsets',ctypes.POINTER(ctypes.c_size_t)),
]
if sys.version_info[:2] < [2.7]:
    # 2.7.5 documentation is incorrect about the structure, it is actually 
    # the Python 3.x version of the struct, so only 2.6 needs the different 
    # form
    _fields_.extend( [
        ('internal',ctypes.c_void_p),
    ] )
else:
    # Sigh, this structure seems to have changed with Python 3.x...
    _fields_.extend( [
        ('smalltable',ctypes.c_size_t*2),
        ('internal',ctypes.c_void_p),
    ] )
class Py_buffer(ctypes.Structure):
    """Wrapper around the Python buffer structure..."""
    _fields_ = _fields_
    @property
    def dims( self ):
        return self.shape[:self.ndim]
#    def __del__( self ):
#        # TODO: use a weakref
#        print 'Releasing'
#        #ReleaseBuffer( self )

BUFFER_POINTER = ctypes.POINTER( Py_buffer )

PyBUF_SIMPLE = 0
PyBUF_WRITABLE = PyBUF_WRITEABLE = 0x0001
PyBUF_ND = 0x0008
PyBUF_STRIDES = (0x0010 | PyBUF_ND)
PyBUF_CONTIG = (PyBUF_ND | PyBUF_WRITABLE)
PyBUF_CONTIG_RO = (PyBUF_ND)

try:
    CheckBuffer = ctypes.pythonapi.PyObject_CheckBuffer
    CheckBuffer.argtypes = [ctypes.py_object]
    CheckBuffer.restype = ctypes.c_int
except AttributeError as err:
    # Python 2.6 doesn't appear to have CheckBuffer support...
    CheckBuffer = lambda x: True

IncRef = ctypes.pythonapi.Py_IncRef 
IncRef.argtypes = [ ctypes.py_object ]
    
GetBuffer = ctypes.pythonapi.PyObject_GetBuffer
GetBuffer.argtypes = [ ctypes.py_object, BUFFER_POINTER, ctypes.c_int ]
GetBuffer.restype = ctypes.c_int

ReleaseBuffer = ctypes.pythonapi.PyBuffer_Release
ReleaseBuffer.argtypes = [ BUFFER_POINTER ]
ReleaseBuffer.restype = None

def test():
    import numpy
    import operator
    try:
        reduce
    except NameError as err:
        from functools import reduce
    buf = Py_buffer()
    # deallocation of the buf causes glibc abort :(
    bufp = ctypes.pointer( buf )
    for x in [
        b'this and that',
        memoryview(b'this'),
        # These are the things you'd have thought might support it...
        #(ctypes.c_int * 3)( 1,2,3 ),
        numpy.arange(0,9,dtype='b').reshape((3,3)),
    ]:
        assert CheckBuffer( x )
        result = GetBuffer( x, bufp, PyBUF_CONTIG_RO )
        buf = bufp[0]
        #IncRef( x ) # No doesn't seem to be due to incref failure
        assert result == 0, "Retrieval of buffer failed"
        print('length:', buf.len)
        print('readonly', buf.readonly)
        print('format', buf.format)
        print('ndim', buf.ndim)
        print('shape', buf.shape[:buf.ndim])
        print('dims', buf.dims )
        print('c data pointer',buf.buf)
        assert buf.len == reduce(operator.__mul__,buf.dims), "Mismatch in size of buffer (%s, expected %s)"%(buf.len,len(x))
        # Always decrefs
        ReleaseBuffer( bufp )
        assert buf.obj == None, buf.obj
    print('finished')
    del bufp 
    del buf
    print('deleted')
if __name__ == "__main__":
    test()
    
