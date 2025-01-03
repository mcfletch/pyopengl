'''OpenGL extension IMG.tile_region_protection

This module customises the behaviour of the 
OpenGL.raw.GLSC2.IMG.tile_region_protection to provide a more 
Python-friendly API

Overview (from the spec)
	
	The safety-critical geometric primitives should have safety 
	mechanisms to guard them against faults that may result in pixel 
	corruption. On Imagination Technologies safety-critical Tile Based 
	rendering GPUs, Tile Region Protection (TRP) safety mechanism 
	performs safety integrity checks on all tiles that contain 
	safety-critical geometries and detect faults in the rendering of 
	these elements. This extension allows application to tag all its 
	safety-critical geometric primitives as safety-related so as to run 
	TRP safety checks on them and report faults in their rendering. 
	Any faults reported by this extension can then be acted upon by the 
	application. Depending on the hardware. TRP can detect either 
	transient or both transient and permanent faults that occur during 
	the rendering of these safety-critical elements.
	
	This extension provides application a way to specify all its 
	safety-critical geometric primitives in order to enable the TRP
	safety integrity checks on them, and thereby detect and report 
	faults in their rendering.
	
	This extension also adds a read-only built-in boolean
	gl_TRPIsProtected, to be used in the fragment shader to check if 
	the tile is protected by TRP or not. This built-in allows 
	developers to verify that all of the safety-critical geometric 
	primitives are indeed protected by TRP. Shaders using the new 
	functionality provided by this extension should enable this via
	the construct,
	
	#extension GL_IMG_tile_region_protection : require   (or enable)

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/IMG/tile_region_protection.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GLSC2 import _types, _glgets
from OpenGL.raw.GLSC2.IMG.tile_region_protection import *
from OpenGL.raw.GLSC2.IMG.tile_region_protection import _EXTENSION_NAME

def glInitTileRegionProtectionIMG():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )


### END AUTOGENERATED SECTION