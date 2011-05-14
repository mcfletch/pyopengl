#! /usr/bin/env python
"""Script to find missing GLUT entry points"""
from OpenGL import GLUT 
import subprocess, re
func_finder = re.compile( 'FGAPIENTRY (\w+)\(' )
constant_finder = re.compile( '#define\W+([0-9a-zA-Z_]+)\W+((0x)?\d+)' )

INCLUDE_DIR = '/usr/include/GL'

def defined( ):
    """Grep FGAPIENTRY headers from /usr/include/GL"""
    pipe = subprocess.Popen( 'grep -r FGAPIENTRY %(INCLUDE_DIR)s/*'%globals(), shell=True, stdout=subprocess.PIPE )
    stdout,stderr = pipe.communicate()
    return stdout
def constants():
    pipe = subprocess.Popen( 'grep -r "#define" %(INCLUDE_DIR)s/*glut*'%globals(), shell=True, stdout=subprocess.PIPE )
    stdout,stderr = pipe.communicate()
    return stdout

def main():
    headers = {}
    for line in defined().splitlines():
        match = func_finder.search( line )
        if match:
            headers[match.group(1)] = line.split(':',1)[0]
    for key in headers.keys():
        if hasattr( GLUT, key ):
            del headers[key]
    import pprint 
    pprint.pprint( headers )
    missing = {}
    for line in constants().splitlines():
        match = constant_finder.search( line )
        if match:
            key,value=(match.group(1),match.group(2))
            if not hasattr( GLUT, key ):
                file = line.split(':',1)[0]
                missing.setdefault(file,[]).append( (key,value))
    for file,variables in missing.items():
        print file
        variables.sort()
        for key,value in variables:
            print '%s=%s'%(key,value)
        

if __name__ == "__main__":
    main()
