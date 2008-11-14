import ctypes
from OpenGL import error

cdef class Wrapper:
	"""C-coded most-generic form of the wrapper's core function"""
	cdef public object calculate_pyArgs, calculate_cArgs, calculate_cArguments, wrappedOperation, storeValues,returnValues
	def __init__( 
		self, wrappedOperation,
		calculate_pyArgs=None, calculate_cArgs=None,
		calculate_cArguments=None, 
		storeValues=None, returnValues=None,
	):
		self.calculate_pyArgs = calculate_pyArgs
		self.calculate_cArgs = calculate_cArgs
		self.calculate_cArguments = calculate_cArguments
		self.wrappedOperation = wrappedOperation
		self.storeValues = storeValues
		self.returnValues = returnValues
	
	def __call__( self, *args ):
		cdef tuple pyArgs, cArgs, cArguments
		if self.calculate_pyArgs is not None:
			pyArgs = tuple(self.calculate_pyArgs( args ))
		else:
			pyArgs = args 
		if self.calculate_cArgs is not None:
			cArgs = tuple(self.calculate_cArgs( pyArgs ))
		else:
			cArgs = pyArgs
		if self.calculate_cArguments is not None:
			cArguments = tuple(self.calculate_cArguments( cArgs ))
		else:
			cArguments = cArgs
		try:
			result = self.wrappedOperation( *cArguments )
		except (ctypes.ArgumentError,TypeError,AttributeError), err:
			err.args = err.args + (cArguments,)
			raise err
		except error.GLError, err:
			err.cArgs = cArgs 
			err.pyArgs = pyArgs
			raise err
		# handle storage of persistent argument values...
		if self.storeValues:
			self.storeValues(
				result,
				self,
				pyArgs,
				cArgs,
			)
		if self.returnValues:
			return self.returnValues(
				result,
				self,
				pyArgs,
				cArgs,
			)
		else:
			return result

cdef class CArgCalculatorElement:
	cdef object wrapper
	cdef long index 
	cdef int callable
	cdef object converter 
	def __init__( self, wrapper, index, converter ):
		self.wrapper = wrapper 
		self.index = index 
		self.converter = converter
		self.callable = callable( converter )
	def __call__( self, pyArgs ):
		"""If callable, call converter( pyArgs, index, wrapper ), else return converter"""
		if self.callable:
			return self.converter( pyArgs, self.index, self.wrapper )
		return self.converter

cdef class CArgCalculator:
	"""C-coded version of the c-arg calculator pattern"""
	cdef list mapping
	def __init__( 
		self,
		wrapper,
		cConverters
	):
		self.mapping = [
			CArgCalculatorElement(self,i,converter)
			for (i,converter) in enumerate( cConverters )
		]
	def __call__( self, pyArgs ):
		result = []
		for calc in self.mapping:
			result.append( calc( pyArgs ) )
		return result
