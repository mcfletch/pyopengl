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

try:
	from OpenGL_accelerate.numpy_accel import dataPointer
except ImportError, err:
	# numpy's array interface has changed over time :(
	testArray = numpy.array( [1,2,3,4],'i' )
	# Numpy's "ctypes" interface actually creates a new ctypes object 
	# in python for every access of the .ctypes attribute... which can take 
	# ridiculously large periods when you multiply it by millions of iterations
#	if hasattr( testArray, 'ctypes' ):
#		if hasattr( testArray.ctypes.data, 'value' ):
#			def dataPointer( cls, instance ):
#				"""Use newer numpy's proper ctypes interface"""
#				try:
#					return instance.ctypes.data.value
#				except AttributeError, err:
#					instance = cls.asArray( instance )
#					return instance.ctypes.data.value
#		else:
#			def dataPointer( cls, instance ):
#				"""Use newer numpy's proper ctypes interface"""
#				try:
#					return instance.ctypes.data
#				except AttributeError, err:
#					instance = cls.asArray( instance )
#					return instance.ctypes.data
	if hasattr(testArray,'__array_interface__'):
		def dataPointer( cls, instance ):
			"""Convert given instance to a data-pointer value (integer)"""
			try:
				return long(instance.__array_interface__['data'][0])
			except AttributeError, err:
				instance = cls.asArray( instance )
				try:
					return long(instance.__array_interface__['data'][0])
				except AttributeError, err:
					return long(instance.__array_data__[0],0)
	else:
		def dataPointer( cls, instance ):
			"""Convert given instance to a data-pointer value (integer)"""
			try:
				return long(instance.__array_data__[0],0)
			except AttributeError, err:
				instance = cls.asArray( instance )
				try:
					return long(instance.__array_interface__['data'][0])
				except AttributeError, err:
					return long(instance.__array_data__[0],0)
	del testArray
	dataPointer = classmethod( dataPointer )

from OpenGL import constants, constant
from OpenGL.arrays import formathandler

class NumpyHandler( formathandler.FormatHandler ):
	"""Numpy-specific data-type handler for OpenGL
	
	Attributes:
	
		ERROR_ON_COPY -- if True, will raise errors 
			if we have to copy an array object in order to produce
			a contiguous array of the correct type.
	"""
	HANDLED_TYPES = (numpy.ndarray,)# list, tuple )
	dataPointer = dataPointer
	isOutput = True
	ERROR_ON_COPY = OpenGL.ERROR_ON_COPY
	@classmethod
	def zeros( cls, dims, typeCode ):
		"""Return Numpy array of zeros in given size"""
		return numpy.zeros( dims, GL_TYPE_TO_ARRAY_MAPPING.get(typeCode) or typeCode )
	@classmethod
	def arrayToGLType( cls, value ):
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
	@classmethod
	def arraySize( cls, value, typeCode = None ):
		"""Given a data-value, calculate dimensions for the array"""
		try:
			dimValue = value.shape
		except AttributeError, err:
			# XXX it's a list or a tuple, how do we determine dimensions there???
			# for now we'll just punt and convert to an array first...
			value = cls.asArray( value, typeCode )
			dimValue = value.shape 
		dims = 1
		for dim in dimValue:
			dims *= dim 
		return dims 
	@classmethod
	def arrayByteCount( cls, value, typeCode = None ):
		"""Given a data-value, calculate number of bytes required to represent"""
		try:
			return cls.arraySize( value, typeCode ) * value.itemsize
		except AttributeError, err:
			value = cls.asArray( value, typeCode )
			return cls.arraySize( value, typeCode ) * value.itemsize
	@classmethod
	def asArray( cls, value, typeCode=None ):
		"""Convert given value to an array value of given typeCode"""
		if value is None:
			return value
		else:
			return cls.contiguous( value, typeCode )

	@classmethod
	def contiguous( cls, source, typeCode=None ):
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
		try:
			contiguous = source.flags.contiguous
		except AttributeError, err:
			if typeCode:
				return numpy.ascontiguousarray( source, typeCode )
			else:
				return numpy.ascontiguousarray( source )
		else:
			if contiguous and (typeCode is None or typeCode==source.dtype.char):
				return source
			elif (contiguous and cls.ERROR_ON_COPY):
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
				if cls.ERROR_ON_COPY:
					from OpenGL import error
					raise error.CopyError(
						"""Non-contiguous array passed""",
						source,
					)
				if typeCode is None:
					typeCode = source.dtype.char
				return numpy.ascontiguousarray( source.astype( typeCode ), typeCode )
	@classmethod
	def unitSize( cls, value, typeCode=None ):
		"""Determine unit size of an array (if possible)"""
		return value.shape[-1]
	@classmethod
	def dimensions( cls, value, typeCode=None ):
		"""Determine dimensions of the passed array value (if possible)"""
		return value.shape
try:
	raise ImportError( 'As of Jan 3, 2009, the FromParam module is causing a weird deallocation failure when the ctypes pointer object tries to clean up the numpy array object (sigh)' )
	from OpenGL_accelerate.numpy_formathandler import FromParam
	from_param = FromParam( NumpyHandler.dataPointer, NumpyHandler.asArray )
	#raise ImportError( """Currently some diff between the Cython and python version causes core dumps""" )
except ImportError, err:
	@classmethod
	def from_param( cls, instance, typeCode=None ):
		try:
			pointer = cls.dataPointer( instance )
		except TypeError, err:
			array = cls.asArray( instance, typeCode )
			pp = cls.dataPointer( array )
			pp._temporary_array_ = (array,)
			return pp
		else:
			return ctypes.c_void_p( pointer )
NumpyHandler.from_param = from_param

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
