import unittest, ctypes
try:
    import numpy 
    from OpenGL_accelerate import numpy_formathandler as npf
except ImportError:
    numpy = None
    npf = None
try:
    from OpenGL_accelerate import buffers_formathandler as bpf
except ImportError:
    bpf = None
from OpenGL import error
from OpenGL import GL
from OpenGL._bytes import integer_types
from OpenGL._configflags import ERROR_ON_COPY
import pytest
pytestmark = pytest.mark.skipif(not numpy, reason="No numpy installed in order to run tests")

class _AccelArray( object ):
    handler_class = None
    def setUp( self ):
        self.array = numpy.array( [[1,2,3],[4,5,6]],'f')
        self.handler = self.handler_class()
    def test_from_param( self ):
        p = self.handler.from_param( self.handler.asArray(self.array ))
        assert isinstance( p, ctypes.c_void_p )
    def test_dataPointer( self ):
        p = self.handler.dataPointer( self.array )
        assert isinstance( p, integer_types)
        assert p == self.array.ctypes.data
    def test_arraySize( self ):
        p = self.handler.arraySize( self.array )
        assert p == 6, p
    def test_arrayByteCount( self ):
        p = self.handler.arrayByteCount( self.array )
        assert p == 24, p
    def test_unitSize( self ):
        p = self.handler.unitSize( self.array )
        assert p == 3, p
    def test_dimensions( self ):
        p = self.handler.dimensions( self.array )
        assert p == (2,3), p
    
    def test_arrayToGLType( self ):
        p = self.handler.arrayToGLType( self.array )
        assert p == GL.GL_FLOAT
        
    

@pytest.mark.skipif(not npf,reason="No numpy native format handler available")
class TestNumpyNative(_AccelArray,unittest.TestCase):
    handler_class = getattr(npf,'NumpyHandler',None)
    def setUp(self):
        super(TestNumpyNative,self).setUp()
        self.eoc_handler = self.handler_class( True )
        
    def test_asArray( self ):
        p = self.handler.asArray( self.array )
        assert p is self.array 
    def test_downconvert( self ):
        p = self.handler.asArray( numpy.array( [1,2,3],'d'), GL.GL_FLOAT )
        assert p.dtype == numpy.float32
    def test_zeros_constant( self ):
        z = self.handler.zeros( (2,3,4), GL.GL_FLOAT)
        assert z.shape == (2,3,4)
        assert z.dtype == numpy.float32
    def test_zeros( self ):
        p = self.handler.zeros( (2,3,4), 'f' )
        assert p.shape == (2,3,4)
        assert p.dtype == numpy.float32
    def test_asArrayCopy( self ):
        a2 = self.array[:,0]
        assert not a2.flags.contiguous 
        self.assertRaises(
            error.CopyError,
            self.eoc_handler.asArray,
                a2
        )
    def test_asArrayConvert( self ):
        self.failUnlessRaises(
            error.CopyError,
            self.eoc_handler.asArray,
                self.array, GL.GL_DOUBLE 
        )
    def test_asArrayConvert( self ):
        p = self.handler.asArray( self.array, GL.GL_DOUBLE )
        assert p is not self.array 
        assert p.dtype == numpy.float64
        p = self.handler.asArray( self.array, 'd' )
        assert p is not self.array 
        assert p.dtype == numpy.float64


@pytest.mark.skipif(not npf,reason="No numpy native format handler available")
class TestBufferAPI(_AccelArray,unittest.TestCase):
    handler_class = getattr(bpf,'MemoryviewHandler',None)
