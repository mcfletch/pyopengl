#! /usr/bin/env python
"""Generate python PyOpenGL api from xml registry documents (using xmlreg)"""
import os, sys, logging, subprocess, glob
import xmlreg, codegenerator
import ctypetopytype

KHRONOS_URL = 'https://cvs.khronos.org/svn/repos/ogl/trunk/doc/registry/public/api/'
KHRONOS_API = os.path.join( os.path.dirname(__file__), '..','..','khronosapi' )

def get_khronos( khronosapi ):
    if not os.path.exists( khronosapi ):
        subprocess.check_call(['svn','co', KHRONOS_URL, khronosapi ])

def main(khronosapi=None):
    khronosapi = khronosapi or KHRONOS_API
    
    files = sorted( glob.glob( os.path.join( khronosapi, '*.xml' ) ))
    for file in files:
        generate_for_file( file )

def generate_for_file( filename ):
    registry = xmlreg.parse( filename )
    generator = codegenerator.Generator(
        registry,
        ctypetopytype.ctype_to_pytype
    )
    for name,feature in registry.feature_set.items():
        print feature.name, feature.api
        generator.module( feature )
    for name,extension in registry.extension_set.items():
        print extension.name, extension.apis
        generator.module( extension )
    if os.path.basename( filename ) == 'gl.xml':
        target = os.path.join( generator.rawTargetDirectory, 'GL','_glgets.py' )
        open( target,'w' ).write( generator.group_sizes())

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
    
