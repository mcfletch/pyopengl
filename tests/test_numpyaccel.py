import unittest, numpy, ctypes
from OpenGL_accelerate import numpy_formathandler as npf
from OpenGL import error

class TestAccelNumpy( unittest.TestCase ):
	def setUp( self ):
		self.array = numpy.array( [[1,2,3],[4,5,6]],'f')
		self.handler = npf.NumpyHandler()
		self.eoc_handler = npf.NumpyHandler( True )
	def test_from_param( self ):
		p = self.handler.from_param( self.array )
		assert isinstance( p, ctypes.c_void_p )
	def test_dataPointer( self ):
		p = self.handler.dataPointer( self.array )
		assert isinstance( p, (int,long))
		assert p == self.array.ctypes.data
	def test_zeros( self ):
		p = self.handler.zeros( (2,3,4), 'f' )
		assert p.shape == (2,3,4)
		assert p.dtype == numpy.float32
	def test_arraySize( self ):
		p = self.handler.arraySize( self.array )
		assert p == 6, p
	def test_arrayByteCount( self ):
		p = self.handler.arrayByteCount( self.array )
		assert p == 24, p
	def test_asArray( self ):
		p = self.handler.asArray( self.array )
		assert p is self.array 
	def test_asArrayConvert( self ):
		p = self.handler.asArray( self.array, 'd' )
		assert p is not self.array 
		assert p.dtype == numpy.float64
	def test_asArrayCopy( self ):
		a2 = self.array[:,0]
		assert not a2.flags.contiguous 
		self.failUnlessRaises(
			error.CopyError,
			self.eoc_handler.asArray,
				a2
		)
	
