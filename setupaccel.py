#!/usr/bin/env python
"""Builds accelleration functions for PyOpenGL
"""
from distutils.core import setup,Extension
try:
	from Cython.Distutils import build_ext
except ImportError, err:
	have_cython = False 
else:
	have_cython = True


import sys, os
sys.path.insert(0, '.' )

def is_package( path ):
	return os.path.isfile( os.path.join( path, '__init__.py' ))
def find_packages( root ):
	"""Find all packages under this directory"""
	for path, directories, files in os.walk( root ):
		if is_package( path ):
			yield path.replace( '/','.' )

extensions = [
]

def cython_extension( name, include_dirs = (), ):
	"""Create a cython extension object"""
	filenames = '%(name)s.c'%locals(), '%(name)s.pyx'%locals()
	filename = filenames[bool(have_cython)]
	return Extension( 
		"OpenGL_accelerate.%(name)s"%locals(),
		[
			os.path.join( 
				'src',
				filename
			),
		],
		include_dirs = ['.','src']+ list(include_dirs)
	)


extensions.extend([
	cython_extension( 'wrapper' ),
	cython_extension( 'formathandler' ),
	cython_extension( 'arraydatatype' ),
	cython_extension( 'errorchecker' ),
	cython_extension( 'vbo' ),
	cython_extension( 'nones_formathandler' ),
])

try:
	import numpy
except ImportError, err:
	sys.stderr.write(
		"""Unable to import numpy, skipping numpy extension building\n"""
	)
else:
	if hasattr( numpy, 'get_include' ):
		includeDirectories = [
			numpy.get_include(),
		]
	else:
		includeDirectories = [
			os.path.join(
				os.path.dirname( numpy.__file__ ),
				'core',
				'include',
			),
		]
	extensions.append( cython_extension( 
		'numpy_formathandler', includeDirectories 
	) )
	
try:
	import Numeric
except ImportError, err:
	sys.stderr.write(
		"""Unable to import Numeric, skipping Numeric extension building\n"""
	)
else:
	definitions = [
		('USE_NUMPY', False ),
	]
	extensions.extend( [
		Extension("OpenGL_accelerate.numeric_accel", [
				os.path.join( 'src', "_arrays.c")
			],
			undefine_macros = definitions,
		),
	])
	

if __name__ == "__main__":
	extraArguments = {
		'classifiers': [
			"""License :: OSI Approved :: BSD License""",
			"""Programming Language :: Python""",
			"""Programming Language :: C""",
			"""Topic :: Software Development :: Libraries :: Python Modules""",
			"""Topic :: Multimedia :: Graphics :: 3D Rendering""",
			"""Intended Audience :: Developers""",
		],
		'keywords': 'PyOpenGL,accelerate',
		'long_description' : """Acceleration code for PyOpenGL

This set of C extensions provides acceleration of common operations
for slow points in PyOpenGL 3.x
""",
		'platforms': ['Win32','Linux','OS-X','Posix'],
	}
	### Now the actual set up call
	if have_cython:
		extraArguments['cmdclass'] = {
			'build_ext': build_ext,
		}
	setup (
		name = "PyOpenGL-accelerate",
		version = "1.0.0b1",
		description = "Acceleration code for PyOpenGL",
		author = "Mike C. Fletcher",
		author_email = "mcfletch@vrplumber.com",
		url = "http://pyopengl.sourceforge.net",
		download_url = "http://sourceforge.net/project/showfiles.php?group_id=5988",
		license = 'BSD',
		packages = list(find_packages( 'OpenGL_accelerate')),
		# non python files of examples      
		ext_modules=extensions,
		**extraArguments
	)
