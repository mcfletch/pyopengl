'''OpenGL extension NV.timeline_semaphore

This module customises the behaviour of the 
OpenGL.raw.GL.NV.timeline_semaphore to provide a more 
Python-friendly API

Overview (from the spec)
	
	The Vulkan API introduces the concept of timeline semaphores.
	This extension brings those concepts to the OpenGL API by adding
	a semaphore type to the semaphore object. In OpenGL, timeline semaphore
	signal and wait operations are similar to the corresponding operations on
	imported Direct3D 12 fences defined in EXT_external_objects_win32.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/NV/timeline_semaphore.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.NV.timeline_semaphore import *
from OpenGL.raw.GL.NV.timeline_semaphore import _EXTENSION_NAME

def glInitTimelineSemaphoreNV():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )

# INPUT glCreateSemaphoresNV.semaphores size not checked against n
glCreateSemaphoresNV=wrapper.wrapper(glCreateSemaphoresNV).setInputArraySize(
    'semaphores', None
)
### END AUTOGENERATED SECTION