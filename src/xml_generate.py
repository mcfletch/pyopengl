#! /usr/bin/env python
"""Generate python PyOpenGL api from xml registry documents (using xmlreg)"""
import os, sys, logging
import xmlreg, generatecode
import ctypetopytype

KHRONOS_API = os.path.join( os.path.dirname(__file__), '..','..','khronosapi' )
DEFAULT_FILES = [
    'gl.xml',
    'glx.xml',
    'wgl.xml',
    'egl.xml',
]

def main(khronosapi=None):
    khronosapi = khronosapi or KHRONOS_API
    files = [ os.path.join( khronosapi, f ) for f in DEFAULT_FILES ]
    for file in files:
        generate_for_file( file )

def generate_for_file( filename ):
    registry = xmlreg.parse( filename )
    generator = generatecode.Generator(
        registry,
        ctypetopytype.ctype_to_pytype
    )
    for name,feature in registry.feature_set.items():
        print feature.name, feature.api
        generator.module( feature )
    for name,extension in registry.extension_set.items():
        print extension.name, extension.apis
        generator.module( extension )
    base_name = os.path.splitext( os.path.basename( filename ))[0]
    open( '%s_sizes.py'%base_name,'w' ).write( generator.group_sizes())

#        for req in feature:
#            if isinstance( req, xmlreg.Require ):
#                if req.profile:
#                    print 'Profile:', req.profile
#                for component in req:
#                    if isinstance( component, xmlreg.Command ):
#                        generator.function( component )
#            else:
#                print 'component', component


if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    main()
    
