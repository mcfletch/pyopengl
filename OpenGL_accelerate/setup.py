#!/usr/bin/env python
"""Builds accelleration functions for PyOpenGL
"""
try:
    from setuptools import setup,Extension
except ImportError, err:
    from distutils.core import setup,Extension
try:
    from Cython.Distutils import build_ext
except ImportError:
    have_cython = False
else:
    have_cython = True


import sys, os
sys.path.insert(0, '.' )

version = None
# get version from __init__.py
for line in open( '__init__.py' ):
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
                'src',
                filename
            ),
        ],
        include_dirs = ['..','src']+ list(include_dirs)
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

try:
    import Numeric
except ImportError:
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
