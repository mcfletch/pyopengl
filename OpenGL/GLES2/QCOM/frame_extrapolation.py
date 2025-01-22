'''OpenGL extension QCOM.frame_extrapolation

This module customises the behaviour of the 
OpenGL.raw.GLES2.QCOM.frame_extrapolation to provide a more 
Python-friendly API

Overview (from the spec)
	
	Frame extrapolation is the process of producing a new, future frame
	based on the contents of two previously rendered frames. It may be
	used to produce high frame rate display updates without incurring the
	full cost of traditional rendering at the higher framerate.
	
	This extension adds support for frame extrapolation in OpenGL ES by
	adding a function which takes three textures. The first two are used
	in sequence as the source frames, from which the extrapolated frame
	is derived. The extrapolated frame is stored in the third texture.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/QCOM/frame_extrapolation.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GLES2 import _types, _glgets
from OpenGL.raw.GLES2.QCOM.frame_extrapolation import *
from OpenGL.raw.GLES2.QCOM.frame_extrapolation import _EXTENSION_NAME

def glInitFrameExtrapolationQCOM():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )


### END AUTOGENERATED SECTION