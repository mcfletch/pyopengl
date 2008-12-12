"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import traceback

cdef class FromParam:
	"""from_param as a helper object"""
	cdef public object dataPointer, asArray
	def __init__( self, dataPointer, asArray ):
		self.dataPointer = dataPointer
		self.asArray = asArray
	def __call__( self, cls, instance, typeCode=None ):
		try:
			try:
				pointer = self.dataPointer( instance )
			except TypeError, err:
				array = self.asArray( instance, typeCode )
				pp = c_void_p( self.dataPointer( array ) )
				pp._temporary_array_ = (array,)
				return pp
			else:
				return c_void_p( pointer )
		except Exception, err:
			traceback.print_exc()
			raise ValueError( 'blah' )
			
