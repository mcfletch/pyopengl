'''OpenGL extension EXT.bindable_uniform

This module customises the behaviour of the 
OpenGL.raw.GL.EXT.bindable_uniform to provide a more 
Python-friendly API
'''
from OpenGL import platform, constants, constant, arrays
from OpenGL import extensions, wrapper
from OpenGL.GL import glget
import ctypes
from OpenGL.raw.GL.EXT.bindable_uniform import *
### END AUTOGENERATED SECTION