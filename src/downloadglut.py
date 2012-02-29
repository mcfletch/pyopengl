#! /usr/bin/env python
"""Download and replicate the Win32+Win64 glut into our DLLs directory...

Visual Studio keeps eating my 64-bit configurations, so we'll use the binary distribution for now...
"""
import sys, os, subprocess, requests, logging, platform, shutil, glob
log = logging.getLogger( 'buildgle' )

DOWNLOAD_URL = 'http://www.idfun.de/glut64/glut-3.7.6-bin-32and64.zip'
GLUT_VERSION = '3.7.6'
GLUT_SOURCE_DIR = 'glut-%(GLUT_VERSION)s-bin'%globals()
ZIP_FILE = '%(GLUT_SOURCE_DIR)s-32and64.zip'%globals()

def download_and_unpack():
    if not os.path.exists( ZIP_FILE ):
        response = requests.get( DOWNLOAD_URL )
        if response.ok:
            open( ZIP_FILE, 'wb').write( response.content )
    if not os.path.exists( GLUT_SOURCE_DIR ):
        subprocess.check_call( 'unzip %(ZIP_FILE)s'%globals() )

def copy():
    current = os.getcwd()
    target_dir = os.path.join( current, '..','OpenGL','DLLS' )
    for fn in glob.glob( os.path.join( GLUT_SOURCE_DIR, '*.dll' )):
        shutil.copyfile( fn, os.path.join( target_dir, os.path.basename( fn )))
    shutil.copyfile( os.path.join( GLUT_SOURCE_DIR, 'README-win32.txt' ), os.path.join( target_dir, 'glut_README.txt' ))

def main():
    download_and_unpack()
    copy()

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
