#! /usr/bin/env python
"""Generate python PyOpenGL api from xml registry documents (using xmlreg)"""
from __future__ import print_function
import os, logging, subprocess, glob
import xmlreg, codegenerator
import ctypetopytype
log = logging.getLogger( 'xml-generate' )

KHRONOS_URL = 'https://github.com/KhronosGroup/OpenGL-Registry.git'
KHRONOS_API = os.path.join( os.path.dirname(__file__), 'khronosapi' )

def get_khronos( khronosapi ):
    if not os.path.exists( khronosapi ):
        subprocess.check_call(['git','clone', KHRONOS_URL, khronosapi ])

def main(khronosapi=None):
    khronosapi = khronosapi or KHRONOS_API
    get_khronos( khronosapi )
    
    files = sorted( glob.glob( os.path.join( khronosapi, 'xml','*.xml' ) ))
    for file in files:
        generate_for_file( file )

def generate_for_file( filename ):
    log.info( 'Starting file: %s', filename )
    registry = xmlreg.parse( filename )
    generator = codegenerator.Generator(
        registry,
        ctypetopytype.ctype_to_pytype
    )
    for name,feature in registry.feature_set.items():
        print(feature.name, feature.api)
        generator.module( feature )
    for name,extension in registry.extension_set.items():
        print(extension.name, extension.apis)
        generator.module( extension )

if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
    
