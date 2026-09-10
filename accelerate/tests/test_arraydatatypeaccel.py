import unittest, ctypes
from OpenGL.arrays import arraydatatype as adt
from OpenGL.arrays import vbo
from OpenGL import GL
from OpenGL._bytes import integer_types
from OpenGL._configflags import ERROR_ON_COPY
import pytest
try:
    import numpy 
except ImportError:
    numpy = None
from OpenGL import acceleratesupport

# Importable is not the same as in use: PYOPENGL_USE_ACCELERATE=0 leaves the
# extension on disk and switches it off, and everything here asks what the
# accelerated handlers do.  ACCELERATE_AVAILABLE is the answer to the question
# these cases are about.
if not acceleratesupport.ACCELERATE_AVAILABLE:
    pytest.skip(
        'the accelerators are not in use here', allow_module_level=True
    )

#: ERROR_ON_COPY is a caller refusing the conversion these are about.
converts_by_copying = pytest.mark.skipif(
    ERROR_ON_COPY, reason='ERROR_ON_COPY refuses the conversion this case is about'
)


class _BaseTest( object ):
    array = None
    def setUp( self ):
        self.handler = adt.ArrayDatatype
        assert self.handler.isAccelerated
    def test_from_param( self ):
        p = self.handler.from_param( self.array )
        assert isinstance( p, ctypes.c_void_p )
    def test_dataPointer( self ):
        p = self.handler.dataPointer( self.array )
        assert isinstance( p, integer_types)
    def test_arraySize( self ):
        p = self.handler.arraySize( self.array )
        assert p == 6, p
    def test_arrayByteCount( self ):
        p = self.handler.arrayByteCount( self.array )
        assert p == 24, p
    def test_asArray( self ):
        p = self.handler.asArray( self.array )
        assert p is self.array 
    def test_unitSize( self ):
        p = self.handler.unitSize( self.array )
        assert p == 3, p
    def test_dimensions( self ):
        p = self.handler.dimensions( self.array )
        assert p == (2,3), p
    
    def test_arrayToGLType( self ):
        p = self.handler.arrayToGLType( self.array )
        assert p == GL.GL_FLOAT

# Skip if modifies the functions, which are *shared* between the 
# classes...
@pytest.mark.skipif( not numpy, reason="Numpy not available")
class TestNumpy( _BaseTest, unittest.TestCase ):
    def setUp( self ):
        super(TestNumpy,self).setUp()
        self.array = numpy.array( [[1,2,3],[4,5,6]],'f')
        handler = adt.ArrayDatatype.getHandler( self.array )
        handler.registerReturn( )

    def test_dataPointer( self ):
        p = self.handler.dataPointer( self.array )
        assert isinstance( p, integer_types)
        assert p == self.array.ctypes.data
    def test_zeros( self ):
        p = self.handler.zeros( (2,3,4), 'f' )
        assert p.shape == (2,3,4)
        assert p.dtype == numpy.float32
    @converts_by_copying
    def test_asArrayConvert( self ):
        p = self.handler.asArray( self.array, GL.GL_DOUBLE )
        assert p is not self.array 
        assert p.dtype == numpy.float64
        p = self.handler.asArray( self.array, 'd' )
        assert p is not self.array 
        assert p.dtype == numpy.float64
    def test_zeros_typed( self ):
        z = self.handler.zeros( (2,3,4), GL.GL_FLOAT)
        assert z.shape == (2,3,4)
        assert z.dtype == numpy.float32
    @converts_by_copying
    def test_downconvert( self ):
        p = self.handler.asArray( numpy.array( [1,2,3],'d'), GL.GL_FLOAT )
        assert p.dtype == numpy.float32
    def test_zeros_small( self ):
        z = self.handler.zeros( (0,), GL.GL_BYTE )
        assert z.dtype == numpy.byte, z

def two_rows_of_three():
    """Six floats in memory a VBO can be made from without a copy.

    Where there is no numpy the array is built and filled rather than
    converted from a list: converting one *is* the copy ERROR_ON_COPY refuses,
    and what these cases are about is the VBO handler rather than the way the
    array beside it was made.
    """
    if numpy:
        return numpy.array( [[1,2,3],[4,5,6]], 'f' )
    array = adt.GLfloatArray.zeros( (2,3) )
    array[0][:] = (1.0,2.0,3.0)
    array[1][:] = (4.0,5.0,6.0)
    return array

class TestVBO( _BaseTest, unittest.TestCase ):
    def setUp( self ):
        self.array = vbo.VBO(two_rows_of_three())
        super(TestVBO,self).setUp()

class TestVBOOffset( _BaseTest, unittest.TestCase ):
    def setUp( self ):
        self.array = vbo.VBO(two_rows_of_three()) + 12
        super(TestVBOOffset,self).setUp()
        
class TestNones( unittest.TestCase ):
    def setUp( self ):
        self.array = None
        self.handler = adt.ArrayDatatype
        assert self.handler.isAccelerated
    def test_from_param( self ):
        p = self.handler.from_param( self.array )
        assert p is None, p
    def test_dataPointer( self ):
        p = self.handler.dataPointer( self.array )
        assert p is None
    def test_asArray( self ):
        p = self.handler.asArray( self.array )
        assert p is self.array 
    def test_dimensions( self ):
        p = self.handler.dimensions( self.array )
        assert p == (0,), p
