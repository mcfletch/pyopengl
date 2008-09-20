"""ctypes abstraction layer

We keep rewriting functions as the main entry points change,
so let's just localise the changes here...
"""
import ctypes, logging
log = logging.getLogger( 'OpenGL.ctypes' )
log.setLevel( logging.DEBUG )
ctypes_version = [
	int(x) for x in ctypes.__version__.split('.')
]
from ctypes import util


def loadLibrary( dllType, name, mode = ctypes.RTLD_GLOBAL ):
	"""Load a given library by name with the given mode
	
	dllType -- the standard ctypes pointer to a dll type, such as
		ctypes.cdll or ctypes.windll or the underlying ctypes.CDLL or 
		ctypes.WinDLL classes.
	name -- a short module name, e.g. 'GL' or 'GLU'
	mode -- ctypes.RTLD_GLOBAL or ctypes.RTLD_LOCAL,
		controls whether the module resolves names via other
		modules already loaded into this process.  GL modules
		generally need to be loaded with GLOBAL flags
	
	returns the ctypes C-module object
	"""
	if ctypes_version > [0,9,9,3]:
		if isinstance( dllType, ctypes.LibraryLoader ):
			dllType = dllType._dlltype
		fullName = None
		try:
			fullName = util.find_library( name )
			if fullName is not None:
				name = fullName
		except Exception, err:
			log.info( '''Failed on util.find_library( %r ): %s''', name, err )
			# Should the call fail, we just try to load the base filename...
			pass
		try:
			return dllType( name, mode )
		except Exception, err:
			err.args += (name,fullName)
			raise
	elif ctypes_version == [0,9,9,3]:
		return dllType.find( name, mode )
	else:
		raise RuntimeError(
			"""Unsupported ctypes version (%s), please upgrade to at least ctypes 0.9.9.3"""%(
				".".join( [str(x) for x in ctypes_version] ),
			)
		)

def buildFunction( functionType, name, dll ):
	"""Abstract away the ctypes function-creation operation"""
	if ctypes_version > [0,9,9,3]:
		return functionType( (name, dll), )
	elif ctypes_version == [0,9,9,3]:
		return functionType( name, dll )
	else:
		raise RuntimeError(
			"""Unsupported ctypes version (%s), please upgrade to at least ctypes 0.9.9.3"""%(
				".".join( [str(x) for x in ctypes_version] ),
			)
		)

