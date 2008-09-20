#! /usr/bin/env python
# if this succeeds, then the pkg_resources are registering properly
import sys,os,glob,pkg_resources

def register_egg_files( ):
	"""Registers egg files in the executable's directory"""
	if sys.frozen:
		directory = os.path.dirname( sys.executable )
		all_eggs = [directory] + glob.glob( '%s/*.egg'%(directory,))
		for source in all_eggs:
			sys.path.append( source )
			pkg_resources.working_set.add_entry( source )
register_egg_files()

import sys,os,ctypes,numpy,pygame
from pygame import display
from ctypes import util
print 'Looking for registered platform implementations'
print 'Registered:', [ e.name for e in pkg_resources.iter_entry_points( "OpenGL.platform.implementation" ) ]
from OpenGL import platform
print 'Able to complete import of platform module'
	