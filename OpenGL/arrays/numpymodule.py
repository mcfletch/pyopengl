"""Numpy (new version) module implementation of the OpenGL-ctypes array interfaces

XXX Need to register handlers for all of the scalar types that numpy returns,
would like to have all return values be int/float if they are of  compatible
type as well.
"""
REGISTRY_NAME = 'numpy'
try:
	import numpy
except ImportError, err:
	raise ImportError( """No numpy module present: %s"""%(err))
import operator
import OpenGL
import ctypes

# numpy's array interface has changed over time :(
testArray = numpy.array( [1,2,3,4],'i' )
if hasattr( testArray, 'ctypes' ):
	if hasattr( testArray.ctypes.data, 'value' ):
		def dataPointer( self, instance ):
			"""Use newer numpy's proper ctypes interface"""
			try:
				return instance.ctypes.data.value
			except AttributeError, err:
				instance = self.asArray( instance )
				return instance.ctypes.data.value
	else:
		def dataPointer( self, instance ):
			"""Use newer numpy's proper ctypes interface"""
			try:
				return instance.ctypes.data
			except AttributeError, err:
				instance = self.asArray( instance )
				return instance.ctypes.data
#	def voidDataPointer( self, instance ):
#		"""Get a void data pointer for the instance"""
#		try:
#			return instance.ctypes.data_as( ctypes.c_void_p )
#		except AttributeError, err:
#			instance = self.asArray( instance )
#			return instance.ctypes.data_as( ctypes.c_void_p )
elif hasattr(testArray,'__array_data__'):
	def dataPointer( self, instance ):
		"""Convert given instance to a data-pointer value (integer)"""
		try:
			return long(instance.__array_data__[0],0)
		except AttributeError, err:
			instance = self.asArray( instance )
			try:
				return long(instance.__array_interface__['data'][0])
			except AttributeError, err:
				return long(instance.__array_data__[0],0)
else:
	def dataPointer( self, instance ):
		"""Convert given instance to a data-pointer value (integer)"""
		try:
			return long(instance.__array_interface__['data'][0])
		except AttributeError, err:
			instance = self.asArray( instance )
			try:
				return long(instance.__array_interface__['data'][0])
			except AttributeError, err:
				return long(instance.__array_data__[0],0)
del testArray

from OpenGL import constants, constant
from OpenGL.arrays import formathandler

class NumpyHandler( formathandler.FormatHandler ):
	"""Numpy-specific data-type handler for OpenGL
	
	Attributes:
	
		ERROR_ON_COPY -- if True, will raise errors 
			if we have to copy an array object in order to produce
			a contiguous array of the correct type.
	"""
	HANDLED_TYPES = (numpy.ndarray, list, tuple )
	dataPointer = dataPointer
	def from_param( self, instance ):
		return ctypes.c_void_p( self.dataPointer( instance ))
	ERROR_ON_COPY = OpenGL.ERROR_ON_COPY
	def zeros( self, dims, typeCode ):
		"""Return Numpy array of zeros in given size"""
		return numpy.zeros( dims, GL_TYPE_TO_ARRAY_MAPPING.get(typeCode) or typeCode )
	def arrayToGLType( self, value ):
		"""Given a value, guess OpenGL type of the corresponding pointer"""
		typeCode = value.dtype.char
		constant = ARRAY_TO_GL_TYPE_MAPPING.get( typeCode )
		if constant is None:
			raise TypeError(
				"""Don't know GL type for array of type %r, known types: %s\nvalue:%s"""%(
					typeCode, ARRAY_TO_GL_TYPE_MAPPING.keys(), value,
				)
			)
		return constant
	def arraySize( self, value, typeCode = None ):
		"""Given a data-value, calculate dimensions for the array"""
		try:
			dimValue = value.shape
		except AttributeError, err:
			# XXX it's a list or a tuple, how do we determine dimensions there???
			# for now we'll just punt and convert to an array first...
			value = self.asArray( value, typeCode )
			dimValue = value.shape 
		dims = 1
		for dim in dimValue:
			dims *= dim 
		return dims 
	def arrayByteCount( self, value, typeCode = None ):
		"""Given a data-value, calculate number of bytes required to represent"""
		try:
			return self.arraySize( value, typeCode ) * value.itemsize
		except AttributeError, err:
			value = self.asArray( value, typeCode )
			return self.arraySize( value, typeCode ) * value.itemsize
	def asArray( self, value, typeCode=None ):
		"""Convert given value to an array value of given typeCode"""
		if value is None:
			return value
		else:
			return self.contiguous( value, typeCode )

	def contiguous( self, source, typeCode=None ):
		"""Get contiguous array from source
		
		source -- numpy Python array (or compatible object)
			for use as the data source.  If this is not a contiguous
			array of the given typeCode, a copy will be made, 
			otherwise will just be returned unchanged.
		typeCode -- optional 1-character typeCode specifier for
			the numpy.array function.
			
		All gl*Pointer calls should use contiguous arrays, as non-
		contiguous arrays will be re-copied on every rendering pass.
		Although this doesn't raise an error, it does tend to slow
		down rendering.
		"""
		typeCode = GL_TYPE_TO_ARRAY_MAPPING.get( typeCode )
		if isinstance( source, numpy.ndarray):
			if source.flags.contiguous and (typeCode is None or typeCode==source.dtype.char):
				return source
			elif (source.flags.contiguous and self.ERROR_ON_COPY):
				from OpenGL import error
				raise error.CopyError(
					"""Array of type %r passed, required array of type %r""",
					source.dtype.char, typeCode,
				)
			else:
				# We have to do astype to avoid errors about unsafe conversions
				# XXX Confirm that this will *always* create a new contiguous array 
				# XXX Guard against wacky conversion types like uint to float, where
				# we really don't want to have the C-level conversion occur.
				# XXX ascontiguousarray is apparently now available in numpy!
				if self.ERROR_ON_COPY:
					from OpenGL import error
					raise error.CopyError(
						"""Non-contiguous array passed""",
						source,
					)
				if typeCode is None:
					typeCode = source.dtype.char
				return numpy.ascontiguousarray( source.astype( typeCode ), typeCode )
		elif typeCode:
			return numpy.ascontiguousarray( source, typeCode )
		else:
			return numpy.ascontiguousarray( source )
	def unitSize( self, value, typeCode=None ):
		"""Determine unit size of an array (if possible)"""
		return value.shape[-1]
	def dimensions( self, value, typeCode=None ):
		"""Determine dimensions of the passed array value (if possible)"""
		return value.shape

try:
	numpy.array( [1], 's' )
	SHORT_TYPE = 's'
except TypeError, err:
	SHORT_TYPE = 'h'
	USHORT_TYPE = 'H'

ARRAY_TO_GL_TYPE_MAPPING = {
	'd': constants.GL_DOUBLE,
	'f': constants.GL_FLOAT,
	'i': constants.GL_INT,
	SHORT_TYPE: constants.GL_SHORT,
	USHORT_TYPE: constants.GL_UNSIGNED_SHORT,
	'B': constants.GL_UNSIGNED_BYTE,
	'c': constants.GL_UNSIGNED_BYTE,
	'b': constants.GL_BYTE,
	'I': constants.GL_UNSIGNED_INT,
}
GL_TYPE_TO_ARRAY_MAPPING = {
	constants.GL_DOUBLE: 'd',
	constants.GL_FLOAT:'f',
	constants.GL_INT: 'i',
	constants.GL_BYTE: 'b',
	constants.GL_SHORT: SHORT_TYPE,
	constants.GL_UNSIGNED_INT: 'I',
	constants.GL_UNSIGNED_BYTE: 'B',
	constants.GL_UNSIGNED_SHORT: USHORT_TYPE,
}
