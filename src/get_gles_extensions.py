#! /usr/bin/env python
"""Get the EGL and ES header files"""
import requests, os, logging, re
from funcparse import Function,Helper
log = logging.getLogger( 'build_gles' )
here = os.path.dirname( __file__ )
HEADER_DIR = os.path.join( here, 'es','include' )
EGL_DIR = os.path.join( here, 'es','egl' )
HEADER_FILES = [
    # EGL 1.4...
    'http://www.khronos.org/registry/egl/api/KHR/khrplatform.h',
    'http://www.khronos.org/registry/egl/api/EGL/egl.h',
    'http://www.khronos.org/registry/egl/api/EGL/eglext.h',
    'http://www.khronos.org/registry/egl/api/EGL/eglplatform.h',
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
        

CONSTANT_DEFINE = re.compile( r'^#define\W+(?P<name>\w+)\W+(?P<value>(0x[0-9a-fA-F]+)|([0-9]+))', re.M )
def find_constants( header ):
    """Given a header, try to find our constants"""
    for constant in CONSTANT_DEFINE.finditer( header ):
        yield constant.groupdict()

def parse_args( args ):
    args = args.strip()
    if args == 'void':
        return []
    else:
        return [parse_arg( a ) for a in args.split(',')]

ARG_PARSE = re.compile( r'^\W*(?P<type>.+?)[ \t]*(?P<name>[a-zA-Z0-9_]+)$', re.DOTALL|re.M)
def parse_arg( arg ):
    arg = arg.strip()
    try:
        arg = ARG_PARSE.search( arg ).groupdict()
    except Exception as err:
        err.args += ( arg, )
        raise
    else:
        arg['type'] = parse_type( arg['type'] )
        return arg

def parse_type( typ ):
    typ = typ.strip()
    if typ.startswith( 'const' ):
        typ = typ[5:].strip()
    indirections = 0
    while typ.endswith( '*' ):
        typ = typ[:-1].strip()
        indirections += 1
    while typ.startswith( 'struct' ):
        typ = typ[6:].strip()
    
    for i in range( indirections ):
        typ = 'pointer(%s)'%( typ, )
    return typ
        
EGL_API = re.compile( r'^EGLAPI[ \t\n](?P<returntype>[a-zA-Z0-9_ *]+)\W+EGLAPIENTRY\W+(?P<name>[_a-z0-9A-Z]+)[ \t]*[(](?P<arguments>[^)]+)[)]', re.M|re.DOTALL )
def egl():
    module = os.path.join( EGL_DIR, 'egl.py' )
    log.info( 'Starting EGL module %s', module )
    khr = open( os.path.join( HEADER_DIR, 'khrplatform.h' ) ).read()
    platform = open( os.path.join( HEADER_DIR, 'eglplatform.h' ) ).read()
    core = open( os.path.join( HEADER_DIR, 'egl.h' ) ).read()
    ext = open( os.path.join( HEADER_DIR, 'eglext.h' ) ).read()
    constants = []
    for header in (khr,platform,core,ext):
        constants.extend( find_constants( header ))
    functions = []
    for header in (core,ext):
        for function in EGL_API.finditer( header ):
            function = function.groupdict()
            function['returntype'] = parse_type( function['returntype'] )
            function = Function( function['returntype'], function['name'], function['arguments'] )
            functions.append( function )
    if not os.path.exists( EGL_DIR ):
        os.makedirs( EGL_DIR )
    with open( module, 'w' ) as fh:
        fh.write('''"""egl wrapper for PyOpenGL"""
from OpenGL import platform as _p
from OpenGL.egl import khr as _cs
from OpenGL import arrays

import ctypes
def _f( function ):
    return _p.createFunction( function,_p.EGL,False)
''')
        for constant in constants:
            fh.write( '%(name)s=%(value)s\n'%constant )
        for function in functions:
            fh.write( function.declaration() )
            fh.write('\n')
            log.debug( '%s', function['name'] )
    log.info( '  %s constants', len(constants))
    if len(functions)<73:
        log.error( 'Expected more functions!' )
    log.info( '  %s functions', len(functions))
        
def main():
    ensure_headers()
    egl()
                
if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
