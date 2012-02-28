#! /usr/bin/env python
"""Build the GLE distribution

Start a VC shell:
    
    "c:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\Visual Studio 2008 Command Prompt.lnk"
    "c:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\Visual Studio 2008 x64 Win64 Command Prompt.lnk"

Then run this script with the appropriate (32-bit or 64-bit python):

    c:\python27-32\python.exe buildgledll.py
    c:\python27-64\python.exe buildgledll.py
"""
import sys, os, subprocess, requests, logging, platform, shutil, glob
log = logging.getLogger( 'buildgle' )

DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/gle/gle/gle-3.1.0/gle-3.1.0.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fgle%2F&ts=1315332658&use_mirror=voxel'
GLE_VERSION = '3.1.0'
GLE_SOURCE_DIR = 'gle-%(GLE_VERSION)s'%globals()
TAR_FILE = '%(GLE_SOURCE_DIR)s.tar.gz'%globals()

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

        outfile = 'opengle%(suffix)s.dll'%locals()

        subprocess.check_call( 'cl -c /D"WIN32" /D "_WINDLL" /Gd /MD *.c' )
        subprocess.check_call( 'link /EXPORT:gleExtrusion /EXPORT:gleGetNumSides /EXPORT:gleSetJoinStyle /EXPORT:glePolyCylinder /EXPORT:gleSpiral /EXPORT:gleSetNumSides /EXPORT:uview_direction /EXPORT:gleScrew /EXPORT:gleHelicoid /EXPORT:gleToroid /EXPORT:urot_omega /EXPORT:rot_about_axis /EXPORT:gleExtrusion /EXPORT:gleTextureMode /EXPORT:urot_prince /EXPORT:rot_prince /EXPORT:gleSuperExtrusion /EXPORT:urot_about_axis /EXPORT:rot_omega /EXPORT:gleLathe /EXPORT:gleGetJoinStyle /EXPORT:glePolyCone /EXPORT:rot_axis /EXPORT:uviewpoint /EXPORT:gleTwistExtrusion /EXPORT:urot_axis /LIBPATH:"C:\Program Files\Microsoft Platform SDK\Lib" /DLL /OUT:%(outfile)s opengl32.lib glu32.lib *.obj'%locals() )

        shutil.copyfile( outfile, os.path.join( current, '..', 'OpenGL','DLLS', outfile ))
        print 'Created file %(outfile)s in OpenGL/DLLS directory'%locals()
        
    finally:
        os.chdir( current )

def main():
    download_and_unpack()
    build()

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()

"""
;REM Batch file to compile GLE as a DLL using Toolkit compiler
;REM Copy to the GLE source directory, i.e.:
;REM 
;REM 	copy buildgledll.bat \csrc\gle-3.1.0\src\
;REM 	vc7.bat
;REM 	buildgledll.bat
;REM 
;REM  Now put the DLL somewhere useful, such as \winnt\system32
;REM 
;REM 	cp gle32.dll \WINNT\system32
;REM 
;REM  Though realistically, we want to package it for regular users
;REM  Download URL: http://downloads.sourceforge.net/project/gle/gle/gle-3.1.0/gle-3.1.0.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fgle%2F&ts=1315332658&use_mirror=voxel
"""