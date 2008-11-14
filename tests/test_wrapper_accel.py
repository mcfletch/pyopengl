#! /usr/bin/env python
"""Tests for the wrapper accelerator..."""
import unittest
from OpenGL import wrapper
from OpenGL_accelerate.wrapper import Wrapper

def reflect( *args ):
	return args

class TestWrapper( unittest.TestCase ):
	def test_simple( self ):
		w = Wrapper( reflect )
		result = w( 1,2 )
		assert result == (1,2), result 
	def test_w_cls( self ):
		class Reflect( object ):
			def __call__( self, *args ):
				return args 
		w = Wrapper( Reflect() )
		result = w( 1,2 )
		assert result == (1,2), result 
	def test_with_pyArgs( self ):
		def calc_py_args( args ):
			return (1,2)
		w = Wrapper( reflect, calculate_pyArgs=calc_py_args )
		result = w( )
		assert result == (1,2), result 
	def test_with_cArgs( self ):
		def calc_c_args( pyargs ):
			return (1,2)
		w = Wrapper( reflect, calculate_cArgs=calc_c_args )
		result = w( )
		assert result == (1,2), result 
	def test_with_cArguments( self ):
		def calc_c_args( pyargs ):
			return (1,2)
		w = Wrapper( reflect, calculate_cArguments=calc_c_args )
		result = w( )
		assert result == (1,2), result 
	

if __name__ == "__main__":
	unittest.main()
	
