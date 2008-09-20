"""Script to initialise all eggs in the current directory for py2exe

PyOpenGL can be used with py2exe, but it needs to be used as an
egg (at the moment) and py2exe doesn't have built-in support for 
using eggs.

To use this script, place it somewhere on your path and then do

	import py2exeeggs
	py2exeeggs.loadEggs()
"""
# first things first, are we running under py2exe?
import imp, os, sys
import pkg_resources as p

def main_is_frozen():
	return (
		hasattr(sys, "frozen") or # new py2exe
		hasattr(sys, "importers") or # old py2exe
		imp.is_frozen("__main__") # tools/freeze
	)

def get_main_dir():
	if main_is_frozen():
		return os.path.dirname(sys.executable)
	return os.path.dirname(sys.argv[0])

def loadEggs( paths = None, ifFrozen=True ):
	"""Load (activate) the eggs on paths
	
	paths -- paths from which to load egg files
		if None use [ get_main_dir() ]
	ifFrozen -- whether to restrict loading to 
		frozen cases (normal case)
	
	returns whether loading was attempted...
	"""
	if ifFrozen and not main_is_frozen():
		return False
	if paths is None:
		paths = [ get_main_dir() ]
	# use an Environment object with a custom search path
	env = p.Environment( list(paths) )
	for dists in env:
		pkgs = env[dists]
		# only activate the newest distribution available
		dist = pkgs.pop(0)
		sys.path.insert(0, dist.location )
		#dist.activate()
	return True

