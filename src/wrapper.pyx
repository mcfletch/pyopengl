import ctypes
from OpenGL import error

cdef extern from "Python.h":
	cdef object PyObject_Type( object )
	cdef object PyDict_GetItem( object, object )
	
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
	def __call__( self, tuple pyArgs ):
		"""If callable, call converter( pyArgs, index, wrapper ), else return converter"""
		return self.c_call( pyArgs )
	cdef object c_call( self, tuple pyArgs ):
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
	def __call__( self, tuple pyArgs ):
		return self.c_call( pyArgs )
	cdef list c_call( self, tuple pyArgs ):
		return [
			(<CArgCalculatorElement> calc).c_call( pyArgs )
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
	def __call__( self, tuple args ):
		"""If converter is not None, call converter( pyArgs[self.index],  wrapper, pyArgs ), else return args[self.index]"""
		return self.c_call( args )
	cdef object c_call( self, tuple args ):
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
		
	def __call__( self, tuple args ):
		return self.c_call( args )
	cdef list c_call( self, tuple args ):
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
			(<PyArgCalculatorElement> calc).c_call( args )
			for calc in self.mapping
		]

cdef class CArgumentCalculator:
	cdef list cResolvers
	cdef int resolver_length
	def __init__( self, cResolvers ):
		self.cResolvers = cResolvers
		self.resolver_length = len(self.cResolvers)
	def __call__( self, tuple cArgs ):
		return self.c_call( cArgs )
	cdef list c_call( self, tuple cArgs ):
		cdef int i
		cdef int resolver_length
		cdef object converter
		if len(cArgs) != self.resolver_length:
			raise TypeError(
				"""Expected %s C arguments for resolution, got %s"""%(
					self.resolver_length,len(cArgs)
				)
			)
		result = [None]*self.resolver_length
		for i in range( self.resolver_length ):
			converter = self.cResolvers[i]
			if converter is None:
				result[i] = cArgs[i]
			else:
				try:
					result[i] = converter( cArgs[i] )
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
	def __call__( self, tuple pyArgs, int index, object wrapper ):
		"""Return pyArgs[self.index] or raise a ValueError"""
		try:
			return pyArgs[ self.index ]
		except IndexError, err:
			raise ValueError(
				"""Expected parameter index %r, but pyArgs only length %s"""%(
				self.index,
				len(pyArgs )
			))

cdef class Wrapper:
	"""C-coded most-generic form of the wrapper's core function
	
	Applies a series of wrapper stages to the core function in order 
	to expand and/or convert parameters into formats which are compatible
	with the underlying (ctypes) library.  Requires the use of the 
	Calculator objects defined later in this module in order to provide 
	efficient operations.
	"""
	cdef CArgCalculator calculate_cArgs
	cdef CArgumentCalculator calculate_cArguments
	cdef PyArgCalculator calculate_pyArgs
	
	cdef public object wrappedOperation, storeValues,returnValues
	cdef int doPyargs, doCargs, doCarguments, doStoreValues, doReturnValues
	def __init__( 
		self, wrappedOperation,
		calculate_pyArgs=None, calculate_cArgs=None,
		calculate_cArguments=None, 
		storeValues=None, returnValues=None,
	):
		if calculate_pyArgs is not None:
			self.calculate_pyArgs = calculate_pyArgs
			self.doPyargs = True
		else:
			self.doPyargs = False
		if calculate_cArgs is not None:
			self.calculate_cArgs = calculate_cArgs
			self.doCargs = True 
		else:
			self.doCargs = False
		if calculate_cArguments is not None:
			self.calculate_cArguments = calculate_cArguments
			self.doCarguments = True
		else:
			self.doCarguments = False
		self.wrappedOperation = wrappedOperation
		self.storeValues = storeValues
		self.returnValues = returnValues
	
	def __call__( self, *args ):
		cdef tuple pyArgs, cArgs, cArguments
		if self.doPyargs:
			pyArgs = tuple(self.calculate_pyArgs.c_call( args ))
		else:
			pyArgs = args 
		if self.doCargs:
			cArgs = tuple(self.calculate_cArgs.c_call( pyArgs ))
		else:
			cArgs = pyArgs
		if self.doCarguments:
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
		if self.storeValues is not None:
			self.storeValues(
				result,
				self,
				pyArgs,
				cArgs,
			)
		if self.returnValues is not None:
			return self.returnValues(
				result,
				self,
				pyArgs,
				cArgs,
			)
		else:
			return result



cdef class getPyArgsName:
	"""CConverter returning named Python argument
	
	Intended for use in cConverters, the function returned 
	retrieves the named pyArg and returns it when called.
	"""
	cdef public unsigned int index
	cdef public str name
	def __init__( self, str name ):
		self.name = name
	def finalise( self, wrapper ):
		self.index = wrapper.pyArgIndex( self.name )
	def __call__( self, tuple pyArgs, int index, object baseOperation ):
		"""Return pyArgs[ self.index ]"""
		return pyArgs[ self.index ]

cdef class returnPyArgument:
	"""ReturnValues returning the named pyArgs value"""
	cdef public unsigned int index
	cdef public str name
	def __init__( self, str name ):
		self.name = name 
	def finalise( self, wrapper ):
		self.index = wrapper.pyArgIndex( self.name )
	def __call__( self, object result, object baseOperation, tuple pyArgs, tuple cArgs ):
		"""Retrieve pyArgs[ self.index ]"""
		return pyArgs[self.index]
cdef class returnPyArgumentIndex:
	cdef public unsigned int index
	def __init__( self, int index ):
		self.index = index
	def finalise( self, wrapper ):
		"""No finalisation required"""
	def __call__( self, object result, object baseOperation, tuple pyArgs, tuple cArgs ):
		"""Retrieve pyArgs[ self.index ]"""
		return pyArgs[self.index]
	
cdef class returnCArgument:
	"""ReturnValues returning the named pyArgs value"""
	cdef public unsigned int index
	cdef public str name
	def __init__( self, str name ):
		self.name = name 
	def finalise( self, wrapper ):
		self.index = wrapper.cArgIndex( self.name )
	def __call__( self, object result, object baseOperation, tuple pyArgs, tuple cArgs ):
		"""Retrieve cArgs[ self.index ]"""
		return cArgs[self.index]
