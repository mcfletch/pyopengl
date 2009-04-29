import ctypes
from OpenGL import error

cdef extern from "Python.h":
	cdef object PyObject_Type( object )
	cdef object PyDict_GetItem( object, object )

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
		return [
			calc( pyArgs )
			for calc in self.mapping
		]

cdef class PyArgCalculatorElement:
	cdef object wrapper
	cdef long index 
	cdef int callable
	cdef object converter 
	def __init__( self, wrapper, index, converter ):
		self.wrapper = wrapper 
		self.index = index 
		self.converter = converter
	def __call__( self, args ):
		"""If callable, call converter( pyArgs, index, wrapper ), else return converter"""
		if self.converter is None:
			return args[self.index]
		try:
			return self.converter( 
				args[self.index], self.wrapper, args 
			)
		except Exception, err:
			if hasattr( err, 'args' ):
				err.args += ( self.converter, )
			raise

cdef class PyArgCalculator:
	"""C-coded version of the py-arg calculator pattern"""
	cdef list mapping
	cdef int length
	cdef object wrapper
	def __init__( 
		self,
		wrapper,
		pyConverters
	):
		self.wrapper = wrapper
		self.mapping = [
			PyArgCalculatorElement(self,i,converter)
			for (i,converter) in enumerate( pyConverters )
		]
		self.length = len(pyConverters)
		
	def __call__( self, args ):
		if self.length != len(args):
			raise ValueError(
				"""%s requires %r arguments (%s), received %s: %r"""%(
					self.wrapper.wrappedOperation.__name__,
					self.length,
					", ".join( self.wrapper.pyConverterNames ),
					len(args),
					args
				)
			)
		return [
			calc( args )
			for calc in self.mapping
		]

cdef class CArgumentCalculator:
	cdef list cResolvers
	def __init__( self, cResolvers ):
		self.cResolvers = cResolvers
	def __call__( self, cArgs ):
		cdef int i
		cdef int resolver_length
		cdef object converter
		resolver_length = len(self.cResolvers )
		if len(cArgs) != resolver_length:
			raise TypeError(
				"""Expected %s C arguments for resolution, got %s"""%(
					resolver_length,len(cArgs)
				)
			)
		result = []
		for i in range( resolver_length ):
			converter = self.cResolvers[i]
			if converter is None:
				result.append( cArgs[i] )
			else:
				try:
					result.append( converter( cArgs[i] ))
				except Exception, err:
					err.args += (converter,)
					raise
		return result


cdef class CallFuncPyConverter:
	"""PyConverter that takes a callable and calls it on incoming"""
	cdef object function
	def __init__( self, function ):
		"""Store the function"""
		self.function = function 
	def __call__( self, incoming, function, argument ):
		"""Call our function on incoming"""
		return self.function( incoming )
cdef class DefaultCConverter:
	cdef int index
	def __init__( self, index ):
		"""Just store index for future access"""
		self.index = index 
	def __call__( self, pyArgs, index, wrapper ):
		"""Return pyArgs[self.index] or raise a ValueError"""
		try:
			return pyArgs[ self.index ]
		except IndexError, err:
			raise ValueError(
				"""Expected parameter index %r, but pyArgs only length %s"""%(
				self.index,
				len(pyArgs )
			))

cdef class getPyArgsName:
	"""CConverter returning named Python argument
	
	Intended for use in cConverters, the function returned 
	retrieves the named pyArg and returns it when called.
	"""
	cdef public unsigned int index
	cdef public str name
	def __init__( self, str name ):
		self.name = name
		self.index = -1
	def finalise( self, wrapper ):
		self.index = wrapper.pyArgIndex( self.name )
	def __call__( self, tuple pyArgs, int index, object baseOperation ):
		"""Return pyArgs[ self.index ]"""
		if self.index == -1:
			self.finalize()
			if self.index == -1:
				raise RuntimeError( """"Did not resolve parameter index for %r"""%(self.name))
		return pyArgs[ self.index ]
