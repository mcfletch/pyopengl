#! /usr/bin/env python
"""Builds links from the OpenGL.org man pages to our "original" directory"""
import os, sys, glob, shutil, re

MAN_TARGET = 'original'
MAN_SOURCES = 'https://cvs.khronos.org/svn/repos/ogl/trunk/ecosystem/public/sdk/docs/man/'
MAN_DIRECTORY = '.man'

def ensure_sources( ):
	"""Ensure that the OpenGL.org man-page sources are available"""
	if not os.path.isdir( MAN_DIRECTORY ):
		os.system( "svn co --username anonymous --password anonymous %s %s"%(
			MAN_SOURCES,
			MAN_DIRECTORY,
		))
		return True
	else:
		cwd = os.getcwd()
		try:
			os.chdir( MAN_DIRECTORY )
			command = 'svn up'
			os.system( command )
		finally:
			os.chdir( cwd )
		return False 

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
	for file in glob.glob( os.path.join( MAN_DIRECTORY,'*.xml' )):
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
	link_sources()
