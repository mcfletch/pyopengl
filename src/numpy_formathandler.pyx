"""Accelerator for numpy format handler operations"""
from ctypes import c_void_p
import traceback, weakref

cdef class ArrayHolder:
	cdef public object array 
	def __init__( self, array ):
		self.array = array 
	def __call__( self, weak ):
		self.array = None

cdef class FromParam:
	"""from_param as a helper object"""
	cdef public object dataPointer, asArray
	cdef list converted
	def __init__( self, dataPointer, asArray ):
		self.dataPointer = dataPointer
		self.asArray = asArray
	def __call__( self, cls, instance, typeCode=None ):
		cdef object pointer
		try:
			pointer = self.dataPointer( instance )
		except TypeError, err:
			array = self.asArray( instance, typeCode )
			dp = self.dataPointer( array )
			pp = c_void_p( dp )
			pp._temporary_array_ = ArrayHolder( array )
			return pp
		else:
			return c_void_p( pointer )
