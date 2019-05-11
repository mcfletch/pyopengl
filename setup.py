#! /usr/bin/env python
"""PyOpenGL setup script (setuptools-based)
"""
import sys, os
extra_commands = {}
try:
    from setuptools import setup 
except ImportError:
    from distutils.core import setup

HERE = os.path.normpath(os.path.abspath(os.path.dirname( __file__ )))
with open(os.path.join(HERE, 'readme.rst'), 'r') as f:
    long_description = f.read()

sys.path.insert(0, '.' )
metadata = dict(
    version = [
        (line.split('=')[1]).strip().strip('"').strip("'")
        for line in open(os.path.join('OpenGL','version.py'))
        if line.startswith( '__version__' )
    ][0],
    author = 'Mike C. Fletcher',
    author_email = 'mcfletch@vrplumber.com',
    url = 'http://pyopengl.sourceforge.net',
    license = 'BSD',
    download_url = "http://sourceforge.net/projects/pyopengl/files/PyOpenGL/",
    keywords = 'Graphics,3D,OpenGL,GLU,GLUT,GLE,GLX,EXT,ARB,Mesa,ctypes',
    classifiers = [
        """License :: OSI Approved :: BSD License""",
        """Programming Language :: Python""",
        """Programming Language :: Python :: 3""",
        """Topic :: Multimedia :: Graphics :: 3D Rendering""",
        """Topic :: Software Development :: Libraries :: Python Modules""",
        """Intended Audience :: Developers""",
    ],
    long_description = long_description,
    long_description_content_type = 'text/x-rst',
)

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

from distutils.command.install_data import install_data
class smart_install_data(install_data):
    def run(self):
        #need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        # should create the directory if it doesn't exist!!!
        return install_data.run(self)
extra_commands['install_data'] = smart_install_data

if sys.platform == 'win32':
    # binary versions of GLUT and GLE for Win32 (sigh)
    DLL_DIRECTORY = os.path.join('OpenGL','DLLS')
    datafiles = [
        (
            DLL_DIRECTORY, [
                os.path.join( DLL_DIRECTORY,file)
                for file in os.listdir( DLL_DIRECTORY )
                if os.path.isfile( file )
            ]
        ),
    ]
else:
    datafiles = []


if __name__ == "__main__":
    setup(
        name = "PyOpenGL",
        packages = list( find_packages('OpenGL') ),
        description = 'Standard OpenGL bindings for Python',
        options = {
            'sdist': {
                'formats': ['gztar','zip'],
                'force_manifest': True,
            },
        },
        data_files = datafiles,
        cmdclass = extra_commands,
        **metadata
    )
