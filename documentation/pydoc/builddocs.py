"""Script to automatically generate PyTable documentation"""
import pydoc2, inspect
from OpenGL import wrapper
from ctypes import _CFuncPtr

originalIsRoutine = inspect.isroutine
def isroutine( obj ):
	"""Allow wrapper objects to show up as functions in pydoc"""
	return (
		isinstance( obj, (wrapper.Wrapper,_CFuncPtr) ) or 
		originalIsRoutine( obj )
	)
inspect.isroutine = isroutine
originalIsBuiltin = inspect.isbuiltin
def isbuiltin( obj ):
	"""Consider ctypes function pointers to be built-ins"""
	return (
		isinstance( obj, (wrapper.Wrapper,_CFuncPtr) ) or 
		originalIsBuiltin( obj )
	)
inspect.isbuiltin = isbuiltin

if __name__ == "__main__":
	excludes = [
		"Numeric",
		"numpy",
		"_tkinter",
		"Tkinter",
		"math",
		"string",
		"pygame",
	]
	stops = [
	]

	modules = [
		'OpenGL',
		'ctypes',
		'__builtin__',
		'OpenGL_accelerate',
	]	
	pydoc2.PackageDocumentationGenerator(
		baseModules = modules,
		destinationDirectory = ".",
		exclusions = excludes,
		recursionStops = stops,
	).process ()
	
