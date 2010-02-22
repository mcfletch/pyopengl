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

from distutils.command.install_data import install_data
class smart_install_data(install_data):
    def run(self):
        #need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        # should create the directory if it doesn't exist!!!
        return install_data.run(self)

if sys.platform == 'win32':
    # binary versions of GLUT and GLE for Win32 (sigh)
    DLL_DIRECTORY = os.path.join('OpenGL','DLLS')
    datafiles = [
        (
            DLL_DIRECTORY, [
                os.path.join( DLL_DIRECTORY,file)
                for file in os.listdir( DLL_DIRECTORY )
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
        cmdclass = {'install_data':smart_install_data},
        **metadata.metadata
    )
