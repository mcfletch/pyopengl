#! /usr/bin/env python
"""Simple setup script that installs Tcl/Tk Togl widget into PyOpenGL"""
import OpenGL,sys, os, shutil, logging, urllib, tarfile, zipfile, fnmatch
import optparse
log = logging.getLogger( 'togl-setup' )

if sys.maxint > 2L**32:
    suffix = '-64'
else:
    suffix = ''
# These three define what software we're going to install...
TOGL_VERSION = '2.0'
COMPILED_TK_VERSION = '8.4'
BASE_URL = 'http://downloads.sourceforge.net/project/togl/Togl'

DOWNLOAD_TEMPLATE = '%(BASE_URL)s/%(TOGL_VERSION)s/Togl%(TOGL_VERSION)s-%(COMPILED_TK_VERSION)s-%%s?use_mirror=iweb'%globals()

urls = {
    'win32': DOWNLOAD_TEMPLATE%('Windows.zip',),
    'linux2': DOWNLOAD_TEMPLATE%('Linux.tar.gz',),
    'linux2-64': DOWNLOAD_TEMPLATE%('Linux64.tar.gz',),
    'darwin': DOWNLOAD_TEMPLATE%('MacOSX.tar.gz',),
}
#urls['linux2-64'] = 'Togl2.0-8.4-Linux64.tar.gz'

WANTED_FILES = 'Togl%(TOGL_VERSION)s-%(COMPILED_TK_VERSION)s-*/lib/Togl%(TOGL_VERSION)s/*'%globals()

def setup( key=None, force=False ):
    """Do setup by creating and populating the directories
    
    This incredibly dumb script is intended to let you unpack 
    the Tcl/Tk library Togl from SourceForce into your 
    PyOpenGL 3.0.1 (or above) distribution.
    
    Note: will not work with win64, both because there is no 
        win64 package and because we don't have a url defined 
        for it.
    """
    if key is None:
        key = '%s%s'%( sys.platform,suffix )
    log.info( 'Doing setup for platform key: %s', key )
    target_directory = os.path.join( 
        os.path.dirname( OpenGL.__file__ ),
        'Tk',
        'togl-%s'%( key, ),
    )
    log.info( 'Target directory: %s', target_directory )
    if key not in urls:
        log.error(
            """URL for platform key %s is not present, please update script""",
            key,
        )
        sys.exit( 1 )
    if os.path.exists( target_directory ):
        return False
    
    url = urls[key]
    log.info( 'Downloading: %s', url )
    filename,headers = urllib.urlretrieve( url )
    log.info( 'Downloaded to: %s', filename )
    if not os.path.isdir( target_directory ):
        log.warn( 'Creating directory: %s', target_directory )
        try:
            os.makedirs( target_directory )
        except OSError, err:
            log.error( "Unable to create directory: %s", target_directory )
            sys.exit( 2 )
    if '.tar.gz' in url:
        log.info( 'Opening TarFile' )
        fh = tarfile.open( filename, 'r:gz')
        def getnames():
            return fh.getnames()
        def getfile( name ):
            return fh.extractfile( name )
    elif '.zip' in url:
        log.info( 'Opening ZipFile' )
        fh = zipfile.ZipFile( filename )
        def getnames():
            return fh.namelist()
        def getfile( name ):
            return fh.open( name )
    try:
        for name in getnames():
            log.debug( 'Found file: %s', name )
            if fnmatch.fnmatch( name, WANTED_FILES ):
                if not name.endswith( '/' ):
                    log.info( 'Found wanted file: %s', name )
                    source = getfile( name )
                    try:
                        new = os.path.join(
                            target_directory,
                            os.path.basename( name ),
                        )
                        log.info( 'Writing file: %s', new )
                        open( new,'wb' ).write( source.read() )
                    finally:
                        if hasattr( source, 'close' ):
                            source.close()
    finally:
        fh.close()
        if filename != url:
            os.remove( filename )
    return True 

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if sys.argv[1:]:
        if sys.argv[1] == 'all':
            keys = urls.keys()
        else:
            keys = sys.arv[1:]
        for key in keys:
            setup( key )
    else:
        setup()
