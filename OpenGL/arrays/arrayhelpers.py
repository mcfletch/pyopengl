"""Helper functions for wrapping array-using operations

These are functions intended to be used in wrapping
GL functions that deal with OpenGL array data-types.
"""
import OpenGL
from OpenGL import contextdata, error, wrapper, constants, converters
from OpenGL.arrays import arraydatatype

if not OpenGL.ERROR_ON_COPY:
	def asArrayType( typ, size=None ):
		"""Create PyConverter to get first argument as array of type"""
		return converters.CallFuncPyConverter( typ.asArray )
else:
	def asArrayType( typ, size=None ):
		"""No converter required"""
		return None
if not OpenGL.ARRAY_SIZE_CHECKING:
	asArrayTypeSize = asArrayType
else:
	try:
		from OpenGL_accelerate.arraydatatype import AsArrayTypedSizeChecked
	except ImportError, err:
		def asArrayTypeSize( typ, size ):
			"""Create PyConverter function to get array as type and check size
			
			Produces a raw function, not a PyConverter instance
			"""
			asArray = typ.asArray
			dataType = typ.typeConstant
			arraySize = typ.arraySize
			def asArraySize( incoming, function, args ):
				handler = typ.getHandler( incoming )
				result = handler.asArray( incoming, dataType )
				actualSize = handler.arraySize(result, dataType)
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
	else:
		asArrayTypeSize = AsArrayTypedSizeChecked

if not OpenGL.ERROR_ON_COPY:
	def asVoidArray( ):
		"""Create PyConverter returning incoming as an array of any type"""
		from OpenGL.arrays import ArrayDatatype
		return converters.CallFuncPyConverter( ArrayDatatype.asArray )
else:
	def asVoidArray( ):
		"""If there's no copying allowed, we can use default passing"""
		return None

class storePointerType( object ):
	"""Store named pointer value in context indexed by constant
	
	pointerName -- named pointer argument 
	constant -- constant used to index in the context storage
	
	Note: OpenGL.STORE_POINTERS can be set with ERROR_ON_COPY
	to ignore this storage operation.
	
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

try:
	from OpenGL_accelerate.wrapper import returnPyArgumentIndex
	returnPointer = returnPyArgumentIndex( 0 )
except ImportError, err:
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
	unitSize = typ.unitSize
	def arraySizeOfFirst( pyArgs, index, baseOperation ):
		"""Return the array size of the first argument"""
		array = pyArgs[0]
		if array is None:
			return default
		else:
			return unitSize( array )
	return arraySizeOfFirst

try:
	from OpenGL_accelerate.arraydatatype import (
		AsArrayOfType,AsArrayTyped,AsArrayTypedSize
	)
except ImportError, err:
	class AsArrayOfType( converters.PyConverter ):
		"""Given arrayName and typeName coerce arrayName to array of type typeName
		
		TODO: It should be possible to drop this if ERROR_ON_COPY,
		as array inputs always have to be the final objects in that 
		case.
		"""
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
		"""Given arrayName and arrayType, convert arrayName to array of type
		
		TODO: It should be possible to drop this if ERROR_ON_COPY,
		as array inputs always have to be the final objects in that 
		case.
		"""
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
		"""Given arrayName and arrayType, determine size of arrayName
		"""
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
