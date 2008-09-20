#! /usr/bin/env python
"""OpenGL-ctypes setup script (setuptools-based)
"""
from setuptools import setup, find_packages
import sys, os
sys.path.insert(0, '.' )
import metadata

requirements = []
if sys.hexversion < 0x2050000:
	requirements.append( 'ctypes' )

if __name__ == "__main__":
	setup(
		name = "PyOpenGL",
		packages = find_packages(),
		
		description = 'Standard OpenGL bindings for Python',
		include_package_data = True,
		exclude_package_data = {
			'': [ '*.odp' ],
		},
		zip_safe = False,
		
		install_requires = requirements,
		options = {
			'sdist': {
				'formats': ['gztar','zip'],
			},
		},
		**metadata.metadata
	)
