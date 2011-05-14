#! /usr/bin/env python
"""Script to find missing GLUT entry points"""
from OpenGL import GLUT 
import subprocess, re
r = re.compile( 'FGAPIENTRY (\w+)\(' )

def defined( ):
    """Grep FGAPIENTRY headers from /usr/include/GL"""
    pipe = subprocess.Popen( 'grep -r FGAPIENTRY /usr/include/GL/*', shell=True, stdout=subprocess.PIPE )
    stdout,stderr = pipe.communicate()
    return stdout

def main():
    headers = {}
    for line in defined().splitlines():
        match = r.search( line )
        if match:
            headers[match.group(1)] = line.split(':',1)[0]
    for key in headers.keys():
        if hasattr( GLUT, key ):
            del headers[key]
    import pprint 
    pprint.pprint( headers )

if __name__ == "__main__":
    main()
