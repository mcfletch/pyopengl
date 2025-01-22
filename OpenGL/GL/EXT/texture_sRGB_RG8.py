'''OpenGL extension EXT.texture_sRGB_RG8

This module customises the behaviour of the 
OpenGL.raw.GL.EXT.texture_sRGB_RG8 to provide a more 
Python-friendly API

Overview (from the spec)
	
	This extension introduces SRG8_EXT as an acceptable internal format.
	This allows efficient sRGB sampling for source images stored with 2
	channels.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/EXT/texture_sRGB_RG8.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.EXT.texture_sRGB_RG8 import *
from OpenGL.raw.GL.EXT.texture_sRGB_RG8 import _EXTENSION_NAME

def glInitTextureSrgbRg8EXT():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )


### END AUTOGENERATED SECTION