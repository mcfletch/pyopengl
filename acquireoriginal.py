#! /usr/bin/env python
"""Builds links from the OpenGL.org man pages to our "original" directory"""
import os, sys, glob, shutil, re, subprocess

MAN_TARGET = 'original'

MAN_SOURCES = [
    ('https://github.com/KhronosGroup/OpenGL-Refpages', 'OpenGL-Refpages'),
]

def ensure_sources( ):
    """Ensure that the OpenGL.org man-page sources are available"""
    for source, target in MAN_SOURCES:
        if not os.path.exists(target):
            subprocess.check_call(
                'git clone %(source)s %(target)s'%locals(),
                shell=True
            )
        else:
            subprocess.check_call(
                'cd %(target)s && git pull --ff-only'%locals(),
                shell=True,
            )

def package_name( name ):
    if name.startswith( 'glX' ):
        return 'GLX'
    elif name.startswith( 'glut' ):
        return 'GLUT'
    elif name.startswith( 'glu' ):
        return 'GLU'
    elif name.startswith( 'gl' ):
        return 'GL'
    else:
        return None


HEADER_KILLER = re.compile( '[<][!]DOCTYPE.*?[>]', re.MULTILINE|re.DOTALL )
def strip_bad_header( data ):
    """Header in the xml files declared from opengl.org doesn't declare namespaces but files use them"""
    match = HEADER_KILLER.search( data )
    if not match:
        import pdb
        pdb.set_trace()
    assert match 
    return data[match.end():]

def link_sources( ):
    """Copy from the MAN_SOURCES directory to "original/package" (heuristic for package)"""
    for source,man_dir in MAN_SOURCES:
        for file in glob.glob( os.path.join( man_dir,'*.xml' )):
            base_name = os.path.basename( file )
            package = package_name( base_name )
            if package:
                old_name = '%s.3G%s'%os.path.splitext( base_name )
                old_path = os.path.join( MAN_TARGET, package, old_name )
                if os.path.exists( old_path ):
                    os.remove( old_path )
                new_path = os.path.join( MAN_TARGET, package, base_name )
                print 'Copying %r\n     To %r'%( base_name, new_path )
                data = open( file ).read()
                stripped = strip_bad_header( data )
                open( new_path,'w').write( stripped )

if __name__ == "__main__":
    ensure_sources()
    # link_sources()
