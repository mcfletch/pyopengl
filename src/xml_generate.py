#! /usr/bin/env python
"""Generate python PyOpenGL api from xml registry documents (using xmlreg)"""
import os, sys, logging
import xmlreg, generatecode
import ctypetopytype

    

def main():
    registry = xmlreg.parse( sys.argv[1] )
    generator = generatecode.Generator(
        ctypetopytype.ctype_to_pytype
    )
    for name,feature in registry.feature_set.items():
        print feature.name, feature.api
        generator.module( feature )
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
    
