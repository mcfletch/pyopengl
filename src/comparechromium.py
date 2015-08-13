#! /usr/bin/env python
"""Script to check our glgetsizes against regal's..."""
from __future__ import print_function
import os, logging, subprocess
import codegenerator, ctypetopytype, xmlreg
log = logging.getLogger( __name__ )
HERE = os.path.dirname( __file__ )
REGAL = os.path.join( HERE, 'regal' )
def update_regal():
    if not os.path.exists( REGAL ):
        command= 'git clone git@github.com:p3/regal.git'
    else:
        command= 'cd %s && git pull'%(REGAL,)
    log.info( 'Running: %s', command )
    subprocess.check_call( command, shell=True )
    return os.path.join( REGAL,'src','apitrace','wrappers','regaltrace.cpp' )

def load_chromium():
    content = open( update_regal() ).read()
    content = content[content.index('_gl_param_size('):]
    content = content.splitlines()[1:]
    mapping = {}
    for line in content:
        line = line.strip()
        if line.startswith( 'default' ):
            break
        if line.startswith( 'case' ):
            line = line[5:]
            var,rvalue = line.split(':')
            var = var.strip()
            rvalue = rvalue.strip().strip(';')
            if rvalue.startswith('return'):
                rvalue = rvalue[6:].strip()
            try:
                rvalue = int( rvalue )
            except ValueError:
                log.warning( 'Complex return for: %s', rvalue )
                continue 
            else:
                if rvalue == 16:
                    rvalue = (4,4)
                else:
                    rvalue = (rvalue,)
            mapping[var] = rvalue
    return mapping
def main():
    chromium = load_chromium()
    registry = xmlreg.parse( os.path.join( HERE,'khronosapi','gl.xml') )
    generator = codegenerator.Generator(
        registry,
        ctypetopytype.ctype_to_pytype
    )
    for key,value in generator.glGetSizes.items():
        if not value:
            if key in chromium:
                print('Updating %s should be %s'%( key, chromium[key] ))
                generator.glGetSizes[key] = [str(chromium[key]).replace(' ','')]
        try:
            chromium.pop(key)
        except KeyError:
            pass 
    for key,value in chromium.items():
        print('New constant from chromium:', (key,value))
        generator.glGetSizes[key] = [str(chromium[key]).replace(' ','')]
    generator.saveGLGetSizes()
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO )
    main()
