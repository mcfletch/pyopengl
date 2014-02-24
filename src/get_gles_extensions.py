#! /usr/bin/env python
"""Get the EGL and ES header files"""
import requests, os, logging, re
from funcparse import Function,Helper
log = logging.getLogger( 'build_gles' )
HERE = os.path.dirname( __file__ )
HEADER_DIR = os.path.join( HERE, 'es','include' )
EGL_DIR = os.path.join( HERE, '..','OpenGL','egl' )

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

EGL_PREFIX = '''"""egl wrapper for PyOpenGL"""
# THIS FILE IS AUTO-GENERATED DO NOT EDIT!
from OpenGL import platform as _p
from OpenGL.khr import *
from OpenGL import khr as _cs
from OpenGL import arrays
from OpenGL.constant import IntConstant as _C
import ctypes

# Callback types, this is a hack to avoid making the 
# khr module depend on the platform or needing to change generator for now...
CALLBACK_TYPE = _p.PLATFORM.functionTypeFor( _p.PLATFORM.EGL )
_cs.EGLSetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )
_cs.EGLGetBlobFuncANDROID = CALLBACK_TYPE( ctypes.c_voidp, EGLsizeiANDROID, ctypes.c_voidp, EGLsizeiANDROID )

EGL_DEFAULT_DISPLAY = EGLNativeDisplayType()
EGL_NO_CONTEXT = EGLContext()
EGL_NO_DISPLAY = EGLDisplay()
EGL_NO_SURFACE = EGLSurface()
EGL_DONT_CARE = -1

def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.EGL,None,False)
'''
EGL_SUFFIX = '''
del ctypes 
del arrays 
'''
    
EGL_API = re.compile( r'^(EGLAPI|GL_APICALL)[ \t\n](?P<returntype>[a-zA-Z0-9_ *]+)\W+(EGLAPIENTRY|GL_APIENTRY)\W+(?P<name>[_a-z0-9A-Z]+)[ \t]*[(](?P<arguments>[^)]+)[)]', re.M|re.DOTALL )
EGL_SUPPRESS = set([
    'eglGetProcAddress',
])

def load_header( header ):
    filename = os.path.join( HEADER_DIR, header )
    if not os.path.exists( filename ):
        raise RuntimeError( "Missing header %s", filename )
    return open( filename ).read()

def write_module( constant_headers, headers, module, suppress=None, prefix=None, suffix=None ):
    suppress = suppress or set()
    
    constant_headers = [load_header(h) for h in constant_headers]
    headers = [load_header(h) for h in headers ]
    
    constants = []
    for header in constant_headers:
        constants.extend( find_constants( header ))
    functions = []
    for header in headers:
        for function in EGL_API.finditer( header ):
            function = function.groupdict()
            #function['returntype'] = parse_type( function['returntype'] )
            function = Function( function['returntype'], function['name'], function['arguments'] )
            if function.name not in suppress:
                functions.append( function )
    if not os.path.exists( os.path.dirname( module ) ):
        os.makedirs( os.path.dirname( module ) )
    with open( module, 'w' ) as fh:
        fh.write(prefix or '')
        for constant in constants:
            fh.write( '%(name)s=_C(%(name)r,%(value)s)\n'%constant )
        for function in functions:
            fh.write( function.declaration() )
            fh.write('\n')
            log.debug( '%s', function['name'] )
        fh.write(suffix or '')
    log.info( 'File: %s', module )
    log.info( '  %s constants', len(constants))
    log.info( '  %s functions', len(functions))

def egl():
    module = os.path.join( EGL_DIR, '__init__.py' )
    log.info( 'Starting EGL module %s', module )
    khr = 'khrplatform.h'
    platform = 'eglplatform.h'
    core = 'egl.h'
    ext = 'eglext.h'
    mesa= 'eglmesaext.h'
    
    write_module( 
        constant_headers = (khr,platform,core,ext,mesa),
        headers= (core,ext,mesa),
        module = module,
        suppress = EGL_SUPPRESS,
        prefix = EGL_PREFIX,
        suffix= EGL_SUFFIX,
    )

GLES_PREFIX = '''"""GLES %(es_version)s wrapper for PyOpenGL"""
from OpenGL import constants as _cs 
from OpenGL import platform as _p
from OpenGL import arrays
from OpenGL.constant import IntConstant as _C
import ctypes

def _f( function ):
    return _p.createFunction( function,_p.GL,None,False)
'''
GLES_SUFFIX = '''
'''
GLES_SUPPRESS = set([
#    'glRenderbufferStorageMultisampleAPPLE', # missing parameter names...
#    'glRenderbufferStorageMultisampleEXT',
#    'glFramebufferTexture2DMultisampleEXT',
])

def gles():
    """Create the GLES 2 and 3 modules"""
    for es_version in (2,3):
        target_dir = os.path.join( HERE, '..', 'OpenGL','es%(es_version)s'%locals() )
        target_module = os.path.join( target_dir, '__init__.py' )
        headers = [ h%locals() for h in [
            'gl%(es_version)s.h','gl%(es_version)sext.h','gl%(es_version)splatform.h']
        ]
        write_module( 
            constant_headers = headers,
            headers= headers,
            module = target_module,
            suppress = GLES_SUPPRESS,
            prefix = GLES_PREFIX%locals(),
            suffix= GLES_SUFFIX,
        )
        
def main():
    ensure_headers()
    egl()
    gles()

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
