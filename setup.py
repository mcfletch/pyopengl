#! /usr/bin/env python
"""OpenGL-ctypes setup script (setuptools-based)
"""
from distutils.core import setup
import sys, os
sys.path.insert(0, '.' )
import metadata

def is_package( path ):
	return os.path.isfile( os.path.join( path, '__init__.py' ))
def find_packages( root ):
	"""Find all packages under this directory"""
	for path, directories, files in os.walk( root ):
		if is_package( path ):
			yield path.replace( '/','.' )

requirements = []
if sys.hexversion < 0x2050000:
	requirements.append( 'ctypes' )

if __name__ == "__main__":
	setup(
		name = "PyOpenGL",
		packages = list( find_packages('OpenGL') ),
		description = 'Standard OpenGL bindings for Python',
		options = {
			'sdist': {
				'formats': ['gztar','zip'],
			},
		},
		**metadata.metadata
	)
