"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import traceback

cdef class FromParam:
	"""from_param as a helper object"""
	cdef public object dataPointer, asArray
	cdef list converted
	def __init__( self, dataPointer, asArray ):
		self.dataPointer = dataPointer
		self.asArray = asArray
	def __call__( self, cls, instance, typeCode=None ):
		try:
			pointer = self.dataPointer( instance )
		except TypeError, err:
			array = self.asArray( instance, typeCode )
			dp = self.dataPointer( array )
#			print 'data pointer', dp, array.__array_interface__['data']
			pp = c_void_p( dp )
			pp.temporary_array = array
			return pp
		else:
			return c_void_p( pointer )
