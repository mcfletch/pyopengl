#! /usr/bin/env python
"""Get the EGL and ES header files"""
import requests, os, logging
log = logging.getLogger( 'build_gles' )
HEADER_DIR = os.path.join( os.path.dirname( __file__ ), 'include' )
HEADER_FILES = [
    # EGL 1.4...
    'http://www.khronos.org/registry/egl/api/EGL/egl.h',
    'http://www.khronos.org/registry/egl/api/EGL/eglext.h',
    'http://www.khronos.org/registry/egl/api/EGL/eglplatform.h',
    'http://www.khronos.org/registry/egl/api/KHR/khrplatform.h',
    # ES 3
    'http://www.khronos.org/registry/gles/api/3.0/gl3.h',
    'http://www.khronos.org/registry/gles/api/3.0/gl3ext.h',
    'http://www.khronos.org/registry/gles/api/3.0/gl3platform.h',
    # ES 2
    'http://www.khronos.org/registry/gles/api/2.0/gl2.h',
    'http://www.khronos.org/registry/gles/api/2.0/gl2ext.h',
    'http://www.khronos.org/registry/gles/api/2.0/gl2platform.h',
]

def ensure_headers( force=False ):
    if not os.path.exists( HEADER_DIR ):
        os.makedirs( HEADER_DIR )
    for url in HEADER_FILES:
        expected = os.path.join( HEADER_DIR, url.split('/')[-1] )
        if force or not os.path.exists( expected ):
            log.info( 'Downloading %s into %s', url, expected )
            response = requests.get( url )
            if response.status_code == 200:
                open( expected, 'w' ).write( response.content )
                log.info( '  Download complete: %s bytes', len(response.content) )
            else:
                log.error( '  Download failed, status code %s: %s', response.status_code, response.content )
                raise RuntimeError( url )

def main():
    ensure_headers()

                
if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
