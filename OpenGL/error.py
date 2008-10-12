"""Implementation of OpenGL errors/exceptions

Note that OpenGL-ctypes will also throw standard errors,
such as TypeError or ValueError when appropriate.

ErrorChecker is an _ErrorChecker instance that allows you
to register a new error-checking function for use 
throughout the system.
"""
import OpenGL
from OpenGL import platform
__all__ = (
	"Error",'GLError','GLUError','GLUTError','glCheckError',
	'GLerror','GLUerror','GLUTerror',
)

class Error( Exception ):
	"""Base class for all PyOpenGL-specific exception classes"""
class CopyError( Error ):
	"""Raised to indicate that operation requires data-copying
	
	Currently only supported by the numpy array formathandler,
	if you set:

		OpenGL.arrays.numpymodule.NumpyHandler.ERROR_ON_COPY = True 
	
	this error will be raised when the Numpy handler is passed
	a numpy array that requires copying to be passed to ctypes.
	"""

class NullFunctionError( Error ):
	"""Error raised when an undefined function is called"""

class GLError( Error ):
	"""OpenGL core error implementation class
	
	Primary purpose of this error class is to allow for 
	annotating an error with more details about the calling 
	environment so that it's easier to debug errors in the
	wrapping process.
	
	Attributes:
	
		err -- the OpenGL error code for the error 
		result -- the OpenGL result code for the operation
		baseOperation -- the "function" being called
		pyArgs -- the translated set of Python arguments
		cArgs -- the Python objects matching 1:1 the C arguments
		cArguments -- ctypes-level arguments to the operation,
			often raw integers for pointers and the like
		description -- OpenGL description of the error (textual)
	"""
	def __init__( 
		self, 
		err=None, 
		result=None, 
		cArguments=None, 
		baseOperation=None, 
		pyArgs=None, 
		cArgs=None,
		description=None,
	):
		"""Initialise the GLError, storing metadata for later display"""
		(
			self.err, self.result, self.cArguments, 
			self.baseOperation, self.pyArgs, self.cArgs,
			self.description
		) = (
			err, result, cArguments,
			baseOperation, pyArgs, cArgs,
			description
		)
	DISPLAY_ORDER = (
		'err', 
		'description',
		'baseOperation',
		'pyArgs', 
		'cArgs',
		'cArguments',
		'result', 
	)
	def __str__( self ):
		"""Create a fully formatted representation of the error"""
		args = []
		for property in self.DISPLAY_ORDER:
			value = getattr( self, property, None )
			if value is not None or property=='description':
				formatFunction = 'format_%s'%(property)
				if hasattr( self, formatFunction ):
					args.append( getattr(self,formatFunction)( property, value ))
				else:
					args.append( '%s = %s'%(
						property,
						self.shortRepr( value ),
					))
		return '%s(\n\t%s\n)'%(self.__class__.__name__, ',\n\t'.join(
			[x for x in args if x]
		))
	def __repr__( self ):
		"""Produce a much shorter version of the error as a string"""
		return '%s( %s )'%(
			self.__class__.__name__,
			", ".join([x for x in [
				'err=%s'%(self.err),
				self.format_description( 'description', self.description ) or '',
				self.format_baseOperation( 'baseOperation', self.baseOperation ) or '',
			] if x])
		)
	def format_description( self, property, value ):
		"""Format description using GLU's gluErrorString"""
		if value is None and self.err is not None:
			try:
				from OpenGL.GLU import gluErrorString
				self.description = value = gluErrorString( self.err )
			except Exception, err:
				return None
		if value is None:
			return None
		return '%s = %s'%(
			property,
			self.shortRepr( value ),
		)
	def shortRepr( self, value, firstLevel=True ):
		"""Retrieve short representation of the given value"""
		if isinstance( value, (list,tuple) ) and value and len(repr(value))>=40:
			if isinstance( value, list ):
				template = '[\n\t\t%s\n\t]'
			else:
				template = '(\n\t\t%s,\n\t)'
			return template%( ",\n\t\t".join(
				[
					self.shortRepr(x,False) for x in value
				]
			))
		r = repr( value )
		if len(r) < 40:
			return r
		else:
			return r[:37] + '...'
	def format_baseOperation( self, property, value ):
		"""Format a baseOperation reference for display"""
		if hasattr( value, '__name__' ):
			return '%s = %s'%( property, value.__name__ )
		else:
			return '%s = %r'%( property, value )

class GLUError( Error ):
	"""GLU error implementation class"""

class GLUTError( Error ):
	"""GLUT error implementation class"""


if OpenGL.ERROR_CHECKING:
	
	class _ErrorChecker( object ):
		"""Global error-checking object
		
		Attributes:
			_registeredChecker -- the checking function enabled when 
				not doing onBegin/onEnd processing
			safeGetError -- platform safeGetError function as callable method
			_currentChecker -- currently active checking function
		"""
		_currentChecker = _registeredChecker = safeGetError = staticmethod( 
			platform.safeGetError 
		)
		def glCheckError( 
			self,
			result,
			baseOperation=None,
			cArguments=None,
			*args
		):
			"""Base GL Error checker compatible with new ctypes errcheck protocol
			
			This function will raise a GLError with just the calling information
			available at the C-calling level, i.e. the error code, cArguments,
			baseOperation and result.  Higher-level code is responsible for any 
			extra annotations.
			
			Note:
				glCheckError relies on glBegin/glEnd interactions to 
				prevent glGetError being called during a glBegin/glEnd 
				sequence.  If you are calling glBegin/glEnd in C you 
				should call onBegin and onEnd appropriately.
			"""
			err = self._currentChecker()
			if err: # GL_NO_ERROR's guaranteed value is 0
				raise GLError(
					err,
					result,
					cArguments = cArguments,
					baseOperation = baseOperation,
				)
			return result
		def nullGetError( self ):
			"""Used as error-checker when inside begin/end set"""
			return None
		def currentChecker( self ):
			"""Return the current error-checking function"""
			return self._currentChecker
		def registerChecker( self, checker=None ):
			"""Explicitly register an error checker
			
			This allows you to, for instance, disable error checking 
			entirely.  onBegin and onEnd will switch between 
			nullGetError and the value registered here.  If checker 
			is None then the default 
			"""
			if checker is None:
				checker = self.safeGetError
			self._registeredChecker = checker
			return checker
		def onBegin( self, target=None ):
			"""Called by glBegin to record the fact that glGetError won't work"""
			self._currentChecker = self.nullGetError
		def onEnd( self, target=None ):
			"""Called by glEnd to record the fact that glGetError will work"""
			self._currentChecker = self._registeredChecker
	
	ErrorChecker = _ErrorChecker()
	
	glCheckError = ErrorChecker.glCheckError
	onBegin = ErrorChecker.onBegin
	onEnd = ErrorChecker.onEnd
else:
	glCheckError = platform.safeGetError

# Compatibility with PyOpenGL 2.x series
GLUerror = GLUError
GLerror = GLError 
GLUTerror = GLUTError
