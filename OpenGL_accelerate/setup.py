#!/usr/bin/env python
"""Builds accelleration functions for PyOpenGL
"""
try:
    from setuptools import setup,Extension
except ImportError:
    from distutils.core import setup,Extension
try:
    from Cython.Distutils import build_ext
except ImportError:
    have_cython = False
else:
    have_cython = True

    

import sys, os

HERE = os.path.normpath(os.path.abspath(os.path.dirname( __file__ )))

version = None
# get version from __init__.py
for line in open( os.path.join( HERE,'__init__.py') ):
    if line.startswith( '__version__' ):
        version = eval(line.split( '=' )[1].strip())
assert version, """Couldn't determine version string!"""

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
                HERE,
                'src',
                filename
            ),
        ],
        include_dirs = [
            os.path.join(HERE,'..'),
            os.path.join(HERE,'src'),
            HERE,
        ]+ list(include_dirs),
        define_macros = [
#            ('NPY_NO_DEPRECATED_API','NPY_1_7_API_VERSION'),
        ],
    )


extensions.extend([
    cython_extension( 'wrapper' ),
    cython_extension( 'formathandler' ),
    cython_extension( 'arraydatatype' ),
    cython_extension( 'errorchecker' ),
    cython_extension( 'vbo' ),
    cython_extension( 'nones_formathandler' ),
    cython_extension( 'latebind' ),
])
if sys.version_info[:2] >= (2,7):
    extensions.extend([
        cython_extension( 'buffers_formathandler' ),
    ])

try:
    import numpy
except ImportError:
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

if __name__ == "__main__":
    extraArguments = {
        'classifiers': [
            """License :: OSI Approved :: BSD License""",
            """Programming Language :: Python""",
            """Programming Language :: Python :: 3""",
            """Programming Language :: C""",
            """Topic :: Software Development :: Libraries :: Python Modules""",
            """Topic :: Multimedia :: Graphics :: 3D Rendering""",
            """Intended Audience :: Developers""",
        ],
        'keywords': 'PyOpenGL,accelerate,Cython',
        'long_description' : """Acceleration code for PyOpenGL

This set of C (Cython) extensions provides acceleration of common operations
for slow points in PyOpenGL 3.x.  For code which uses large arrays extensively
speed-up is around 10% compared to unaccelerated code.
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
        version = version,
        description = "Acceleration code for PyOpenGL",
        author = "Mike C. Fletcher",
        author_email = "mcfletch@vrplumber.com",
        url = "http://pyopengl.sourceforge.net",
        download_url = "http://sourceforge.net/project/showfiles.php?group_id=5988",
        license = 'BSD',
        packages = ['OpenGL_accelerate'],
        options = {
            'sdist': {
                'formats': ['gztar','zip'],
                'force_manifest': True,
            },
        },
        package_dir = {
            'OpenGL_accelerate':'.',
        },
        ext_modules=extensions,
        **extraArguments
    )
