#class LazyWrapper( object ):
#	"""Object which holds a lazy-loading function and a wrapper object
#	
#	Applies the wrapper to the baseFunction when the baseFunction is 
#	defined, otherwise just calls the base function.
#	"""
#	def __init__( self, baseFunction, wrapperFunction ):
#		"""Initialize the lazy wrapper 
#		
#		baseFunction -- the base platform function object 
#		wrapperFunction -- the wrapper function, must take 
#			the baseFunction as its first argument, then the arguments
#			for the Pythonic API for the function
#		"""
#		self.baseFunction = baseFunction
#		self.wrapperFunction = wrapperFunction
#	def __call__( self, *args, **named ):
#		if self.baseFunction:
#			return self.wrapperFunction( self.baseFunction, *args, **named )
#		else:
#			return self.baseFunction( *args, **named )
#	def __nonzero__( self ):
#		return bool( self.baseFunction )

def lazy( baseFunction ):
	"""Produce a lazy-binding decorator that uses baseFunction
	"""
	def wrap( wrapper ):
		"""Wrap wrapper with baseFunction"""
		def __call__( self, *args, **named ):
			if baseFunction:
				return wrapper( baseFunction, *args, **named )
			else:
				return baseFunction( *args, **named )
		def __nonzero__( self ):
			return bool( baseFunction )
		_with_wrapper = type( wrapper.__name__, (object,), {
			'__call__': __call__,
			'__doc__': wrapper.__doc__,
			'__nonzero__': __nonzero__,
			'restype': getattr(wrapper, 'restype',getattr(baseFunction,'restype',None)),
		} )
		with_wrapper = _with_wrapper()
		with_wrapper.__name__ = wrapper.__name__
		with_wrapper.baseFunction = baseFunction 
		with_wrapper.wrapperFunction = wrapper
		return with_wrapper
	return wrap 


if __name__ == "__main__":
	from OpenGL.raw import GLU
	func = GLU.gluNurbsCallbackData
	output = []
	def testwrap( base ):
		"Testing"
		output.append( base )
	testlazy = lazy( func )( testwrap )
	testlazy( )
	assert testlazy.__doc__ == "Testing" 
	assert testlazy.__class__.__name__ == 'testwrap'
	assert testlazy.__name__ == 'testwrap'
	assert testlazy.baseFunction is func 
	assert testlazy.wrapperFunction is testwrap
	assert output 
