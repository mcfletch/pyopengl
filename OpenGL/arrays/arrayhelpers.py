"""Helper functions for wrapping array-using operations

These are functions intended to be used in wrapping
GL functions that deal with OpenGL array data-types.
"""
from OpenGL import contextdata, error, wrapper, constants, converters
from OpenGL.arrays import arraydatatype

def asArrayType( typ ):
	"""Create PyConverter to get first argument as array of type"""
	return converters.CallFuncPyConverter( typ.asArray )

def typedPointer( typ, ctyp ):
	"""Create a CResolver to get argument as a pointer to the ctypes type ctyp
	
	i.e. typedPointer( arrays.UIntArray, ctypes.c_uint )
	"""
	import ctypes
	ctyp = ctypes.POINTER( ctyp )
	def typedPointerConverter(  value ):
		"""Get the arg as an array of the appropriate type"""
		return ctypes.cast( typ.dataPointer(value), ctyp)
	return typedPointerConverter
	
def asArrayTypeSize( typ, size ):
	"""Create PyConverter function to get array as type and check size
	
	Produces a raw function, not a PyConverter instance
	"""
	asArray = typ.asArray
	arraySize = typ.arraySize
	def asArraySize( incoming, function, args ):
		result = asArray( incoming )
		actualSize = arraySize(result)
		if actualSize != size:
			raise ValueError(
				"""Expected %r item array, got %r item array"""%(
					size,
					actualSize,
				),
				incoming,
			)
		return result
	return asArraySize

def asVoidArray( ):
	"""Create PyConverter returning incoming as an array of any type"""
	from OpenGL.arrays import ArrayDatatype
	return converters.CallFuncPyConverter( ArrayDatatype.asArray )

class storePointerType( object ):
	"""Store named pointer value in context indexed by constant
	
	pointerName -- named pointer argument 
	constant -- constant used to index in the context storage
	
	Stores the pyArgs (i.e. result of pyConverters) for the named
	pointer argument...
	"""
	def __init__( self, pointerName, constant ):
		self.pointerName = pointerName
		self.constant = constant 
	def finalise( self, wrapper ):
		self.pointerIndex = wrapper.pyArgIndex( self.pointerName )
	def __call__( self, result, baseOperation, pyArgs, cArgs ):
		contextdata.setValue( self.constant, pyArgs[self.pointerIndex] )

def returnPointer( result,baseOperation,pyArgs,cArgs, ):
	"""Return the converted object as result of function
	
	Note: this is a hack that always returns pyArgs[0]!
	"""
	return pyArgs[0]

def setInputArraySizeType( baseOperation, size, type, argName=0 ):
	"""Decorate function with vector-handling code for a single argument
	
	This assumes *no* argument expansion, i.e. a 1:1 correspondence...
	"""
	function = wrapper.wrapper( baseOperation )
	if not hasattr( function, 'returnValues' ):
		function.setReturnValues( returnPointer )
	if size is not None:
		function.setPyConverter( argName, asArrayTypeSize(type, size) )
	else:
		function.setPyConverter( argName, asArrayType(type) )
	function.setCConverter( argName, converters.getPyArgsName( argName ) )
	return function

def arraySizeOfFirstType( typ, default ):
	def arraySizeOfFirst( pyArgs, index, baseOperation ):
		"""Return the array size of the first argument"""
		array = pyArgs[0]
		if array is None:
			return default
		else:
			return typ.unitSize( array )
	return arraySizeOfFirst

class AsArrayOfType( converters.PyConverter ):
	"""Given arrayName and typeName coerce arrayName to array of type typeName"""
	argNames = ( 'arrayName','typeName' )
	indexLookups = ( 
		('arrayIndex', 'arrayName','pyArgIndex'),
		('typeIndex', 'typeName','pyArgIndex'),
	)
	def __init__( self, arrayName='pointer', typeName='type' ):
		self.arrayName = arrayName
		self.typeName = typeName 
	def __call__( self, arg, wrappedOperation, args):
		"""Get the arg as an array of the appropriate type"""
		type = args[ self.typeIndex ]
		arrayType = arraydatatype.GL_CONSTANT_TO_ARRAY_TYPE[ type ]
		return arrayType.asArray( arg )
class AsArrayTyped( converters.PyConverter ):
	"""Given arrayName and arrayType, convert arrayName to array of type"""
	argNames = ( 'arrayName','arrayType' )
	indexLookups = ( 
		('arrayIndex', 'arrayName','pyArgIndex'),
	)
	def __init__( self, arrayName='pointer', arrayType=None ):
		self.arrayName = arrayName
		self.arrayType = arrayType
	def __call__( self, arg, wrappedOperation, args):
		"""Get the arg as an array of the appropriate type"""
		return self.arrayType.asArray( arg )
class AsArrayTypedSize( converters.CConverter ):
	"""Given arrayName and arrayType, determine size of arrayName"""
	argNames = ( 'arrayName','arrayType' )
	indexLookups = ( 
		('arrayIndex', 'arrayName','pyArgIndex'),
	)
	def __init__( self, arrayName='pointer', arrayType=None ):
		self.arrayName = arrayName
		self.arrayType = arrayType
	def __call__( self, pyArgs, index, wrappedOperation ):
		"""Get the arg as an array of the appropriate type"""
		return self.arrayType.arraySize( pyArgs[self.arrayIndex ] )
