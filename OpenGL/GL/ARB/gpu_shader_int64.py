'''OpenGL extension ARB.gpu_shader_int64

This module customises the behaviour of the 
OpenGL.raw.GL.ARB.gpu_shader_int64 to provide a more 
Python-friendly API

Overview (from the spec)
	
	The extension introduces the following features for all shader types:
	
	  * support for 64-bit scalar and vector integer data types, including
	    uniform API, uniform buffer object, transform feedback, and shader
	    input and output support;
	
	  * new built-in functions to pack and unpack 64-bit integer types into a
	    two-component 32-bit integer vector;
	
	  * new built-in functions to convert double-precision floating-point
	    values to or from their 64-bit integer bit encodings;
	
	  * vector relational functions supporting comparisons of vectors of
	    64-bit integer types; and
	
	  * common functions abs, sign, min, max, clamp, and mix supporting
	    arguments of 64-bit integer types.
	

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/ARB/gpu_shader_int64.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.ARB.gpu_shader_int64 import *
from OpenGL.raw.GL.ARB.gpu_shader_int64 import _EXTENSION_NAME

def glInitGpuShaderInt64ARB():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )

# INPUT glUniform1i64vARB.value size not checked against count
glUniform1i64vARB=wrapper.wrapper(glUniform1i64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform2i64vARB.value size not checked against count*2
glUniform2i64vARB=wrapper.wrapper(glUniform2i64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform3i64vARB.value size not checked against count*3
glUniform3i64vARB=wrapper.wrapper(glUniform3i64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform4i64vARB.value size not checked against count*4
glUniform4i64vARB=wrapper.wrapper(glUniform4i64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform1ui64vARB.value size not checked against count
glUniform1ui64vARB=wrapper.wrapper(glUniform1ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform2ui64vARB.value size not checked against count*2
glUniform2ui64vARB=wrapper.wrapper(glUniform2ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform3ui64vARB.value size not checked against count*3
glUniform3ui64vARB=wrapper.wrapper(glUniform3ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glUniform4ui64vARB.value size not checked against count*4
glUniform4ui64vARB=wrapper.wrapper(glUniform4ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glGetUniformi64vARB.params size not checked against 'program,location'
glGetUniformi64vARB=wrapper.wrapper(glGetUniformi64vARB).setInputArraySize(
    'params', None
)
# INPUT glGetUniformui64vARB.params size not checked against 'program,location'
glGetUniformui64vARB=wrapper.wrapper(glGetUniformui64vARB).setInputArraySize(
    'params', None
)
# INPUT glProgramUniform1i64vARB.value size not checked against count
glProgramUniform1i64vARB=wrapper.wrapper(glProgramUniform1i64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform2i64vARB.value size not checked against count*2
glProgramUniform2i64vARB=wrapper.wrapper(glProgramUniform2i64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform3i64vARB.value size not checked against count*3
glProgramUniform3i64vARB=wrapper.wrapper(glProgramUniform3i64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform4i64vARB.value size not checked against count*4
glProgramUniform4i64vARB=wrapper.wrapper(glProgramUniform4i64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform1ui64vARB.value size not checked against count
glProgramUniform1ui64vARB=wrapper.wrapper(glProgramUniform1ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform2ui64vARB.value size not checked against count*2
glProgramUniform2ui64vARB=wrapper.wrapper(glProgramUniform2ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform3ui64vARB.value size not checked against count*3
glProgramUniform3ui64vARB=wrapper.wrapper(glProgramUniform3ui64vARB).setInputArraySize(
    'value', None
)
# INPUT glProgramUniform4ui64vARB.value size not checked against count*4
glProgramUniform4ui64vARB=wrapper.wrapper(glProgramUniform4ui64vARB).setInputArraySize(
    'value', None
)
### END AUTOGENERATED SECTION