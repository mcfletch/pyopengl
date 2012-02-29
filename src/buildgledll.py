#! /usr/bin/env python
"""Build the (Open)GLE distribution

Start a VC shell:
    
    "c:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\Visual Studio 2008 Command Prompt.lnk"
    "c:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\Visual Studio 2008 x64 Win64 Command Prompt.lnk"

Then run this script with the appropriate (32-bit or 64-bit python):

    c:\python27-32\python.exe buildgledll.py
    c:\python27-64\python.exe buildgledll.py

Note: the name "opengle" is required because someone issues DMCA takedown orders against anything named "gle.dll"
despite the name GLE referring to the GLE project for a very long time (they took PyOpenGL offline for a while
due to such a takedown notice).
"""
import sys, os, subprocess, requests, logging, platform, shutil, glob
log = logging.getLogger( 'buildgle' )

DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/gle/gle/gle-3.1.0/gle-3.1.0.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fgle%2F&ts=1315332658&use_mirror=voxel'
GLE_VERSION = '3.1.0'
GLE_SOURCE_DIR = 'gle-%(GLE_VERSION)s'%globals()
TAR_FILE = '%(GLE_SOURCE_DIR)s.tar.gz'%globals()
EXPORTS = """
gleExtrusion gleGetNumSides gleSetJoinStyle glePolyCylinder gleSpiral gleSetNumSides uview_direction gleScrew
gleHelicoid gleToroid gleExtrusion gleTextureMode gleSuperExtrusion gleLathe gleGetJoinStyle glePolyCone gleTwistExtrusion 
urot_omega rot_about_axis urot_prince rot_prince urot_about_axis rot_omega rot_axis uviewpoint urot_axis"""

if sys.hexversion < 0x2070000:
    VC = 'vc7'
# TODO: add Python 3.x compiler compatibility...
else:
    VC = 'vc9'

def download_and_unpack():
    if not os.path.exists( TAR_FILE ):
        response = requests.get( DOWNLOAD_URL )
        if response.ok:
            open( TAR_FILE, 'wb').write( response.content )
    if not os.path.exists( GLE_SOURCE_DIR ):
        subprocess.check_call( 'tar -zxvf %(TAR_FILE)s'%globals() )

def size():
    return platform.architecture()[0].strip( 'bits' )

def build():
    current = os.getcwd()
    suffix = size()
    shutil.copyfile( os.path.join( GLE_SOURCE_DIR, 'ms-visual-c', 'config.h' ), os.path.join(GLE_SOURCE_DIR,'config.h') )
    shutil.copyfile( os.path.join( GLE_SOURCE_DIR, 'ms-visual-c', 'config.h' ), os.path.join(GLE_SOURCE_DIR,'src','config.h') )
    os.chdir( os.path.join( GLE_SOURCE_DIR, 'src' ))
    try:
        for file in glob.glob( '*.obj' ):
            os.remove( file )
        for file in glob.glob( '*%(suffix)s.dll'%locals() ):
            os.remove( file )

        vc = VC
        outfile = 'opengle%(suffix)s.%(vc)s.dll'%locals()
        target = os.path.join( current, '..', 'OpenGL','DLLS', outfile )
        exports = " ".join([ '/EXPORT:%s'%(x) for x in EXPORTS.split() if x])

        subprocess.check_call( 'cl -c /D"WIN32" /D "_WINDLL" /Gd /MD *.c' )
        subprocess.check_call( 'link  /LIBPATH:"C:\Program Files\Microsoft Platform SDK\Lib" %(exports)s /DLL /OUT:%(outfile)s opengl32.lib glu32.lib *.obj'%locals() )

        shutil.copyfile( outfile, target )
        print 'Created file %(target)s'%locals()
        
    finally:
        os.chdir( current )

def main():
    download_and_unpack()
    build()

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
