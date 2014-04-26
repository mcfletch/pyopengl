#! /usr/bin/env python
"""Python 3.x buffer-handling (currently just for bytes/bytearray types)
"""
import ctypes,sys
if sys.version_info[:2] < (2,6):
    raise ImportError( 'Buffer interface only usable on Python 2.6+' )

PyBUF_SIMPLE = 0
PyBUF_WRITABLE = PyBUF_WRITEABLE = 0x0001
PyBUF_ND = 0x0008
PyBUF_STRIDES = (0x0010 | PyBUF_ND)
PyBUF_CONTIG = (PyBUF_ND | PyBUF_WRITABLE)
PyBUF_CONTIG_RO = (PyBUF_ND)
PyBUF_C_CONTIGUOUS = (0x0020 | PyBUF_STRIDES)
PyBUF_FORMAT = 0x0004
    
_fields_ = [
    ('buf',ctypes.c_void_p),
    ('obj',ctypes.c_void_p),
    ('len',ctypes.c_ssize_t),
    ('itemsize',ctypes.c_ssize_t),

    ('readonly',ctypes.c_int),
    ('ndim',ctypes.c_int),
    ('format',ctypes.c_char_p),
    ('shape',ctypes.POINTER(ctypes.c_ssize_t)),
    ('strides',ctypes.POINTER(ctypes.c_ssize_t)),
    ('suboffsets',ctypes.POINTER(ctypes.c_ssize_t)),
]


if sys.version_info[:2] <= (2,6) or sys.version_info[:2] >= (3,3):
    # Original structure was eventually restored in 3.3, so just 
    # 2.7 through 3.2 uses the "enhanced" structure below
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
    @classmethod 
    def from_object( cls, object, flags=PyBUF_STRIDES|PyBUF_FORMAT|PyBUF_C_CONTIGUOUS ):
        """Create a new Py_buffer referencing ram of object"""
        if not CheckBuffer( object ):
            raise TypeError( "%s type does not support Buffer Protocol"%(object.__class__,))
        buf = cls()
        # deallocation of the buf causes glibc abort :(
        result = GetBuffer( object, buf, flags )
        if result != 0:
            raise ValueError( "Unable to retrieve Buffer from %s"%(object,))
        if not buf.buf:
            raise ValueError( "Null pointer result from %s"%(object,) )
        return buf
    _fields_ = _fields_
    @property
    def dims( self ):
        return self.shape[:self.ndim]
    def __len__( self ):
        return self.shape[0]
    @property 
    def dim_strides( self ):
        if self.strides:
            return self.strides[:self.ndim]
        return None
    def __enter__(self):
        pass 
    def __exit__( self, exc_type=None, exc_value=None, traceback=None):    
        if self.obj:
            ReleaseBuffer( self )
    def __del__( self ):
        if self.obj:
            ReleaseBuffer( self )
    
BUFFER_POINTER = ctypes.POINTER( Py_buffer )


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

BYTE_SIZES = {
    0x1400: 1,#GL_BYTE
    0x1401: 1,#GL_UNSIGNED_BYTE
    0x1402: 2,#GL_SHORT
    0x1403: 2,#GL_UNSIGNED_SHORT
    0x1404: 4,#GL_INT
    0x1405: 4,#GL_UNSIGNED_INT
    0x1406: 4,#GL_FLOAT
    0x140a: 8,#GL_DOUBLE
}

ARRAY_TO_GL_TYPE_MAPPING = {
    'c': 0x1401,#GL_UNSIGNED_BYTE
    'f': 0x1406,#GL_FLOAT
    'b': 0x1400,#GL_BYTE
    'i': 0x1404,#GL_INT
    'l': 0x1404,#GL_INT
    '?': 0x1404,#GL_INT # Boolean 
    'd': 0x140a,#GL_DOUBLE
    'L': 0x1405,#GL_UNSIGNED_INT
    'h': 0x1402,#GL_SHORT
    'H': 0x1403,#GL_UNSIGNED_SHORT
    'B': 0x1401,#GL_UNSIGNED_BYTE
    'I': 0x1405,#GL_UNSIGNED_INT    
    None: None,
}
