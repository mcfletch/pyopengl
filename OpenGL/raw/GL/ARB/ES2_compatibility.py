'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_ARB_ES2_compatibility'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_ARB_ES2_compatibility',error_checker=_errors._error_checker)
GL_FIXED=_C('GL_FIXED',0x140C)
GL_HIGH_FLOAT=_C('GL_HIGH_FLOAT',0x8DF2)
GL_HIGH_INT=_C('GL_HIGH_INT',0x8DF5)
GL_IMPLEMENTATION_COLOR_READ_FORMAT=_C('GL_IMPLEMENTATION_COLOR_READ_FORMAT',0x8B9B)
GL_IMPLEMENTATION_COLOR_READ_TYPE=_C('GL_IMPLEMENTATION_COLOR_READ_TYPE',0x8B9A)
GL_LOW_FLOAT=_C('GL_LOW_FLOAT',0x8DF0)
GL_LOW_INT=_C('GL_LOW_INT',0x8DF3)
GL_MAX_FRAGMENT_UNIFORM_VECTORS=_C('GL_MAX_FRAGMENT_UNIFORM_VECTORS',0x8DFD)
GL_MAX_VARYING_VECTORS=_C('GL_MAX_VARYING_VECTORS',0x8DFC)
GL_MAX_VERTEX_UNIFORM_VECTORS=_C('GL_MAX_VERTEX_UNIFORM_VECTORS',0x8DFB)
GL_MEDIUM_FLOAT=_C('GL_MEDIUM_FLOAT',0x8DF1)
GL_MEDIUM_INT=_C('GL_MEDIUM_INT',0x8DF4)
GL_NUM_SHADER_BINARY_FORMATS=_C('GL_NUM_SHADER_BINARY_FORMATS',0x8DF9)
GL_RGB565=_C('GL_RGB565',0x8D62)
GL_SHADER_BINARY_FORMATS=_C('GL_SHADER_BINARY_FORMATS',0x8DF8)
GL_SHADER_COMPILER=_C('GL_SHADER_COMPILER',0x8DFA)
@_f
@_p.types(None,_cs.GLfloat)
def glClearDepthf(d):pass
@_f
@_p.types(None,_cs.GLfloat,_cs.GLfloat)
def glDepthRangef(n,f):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,arrays.GLintArray,arrays.GLintArray)
def glGetShaderPrecisionFormat(shadertype,precisiontype,range,precision):pass
@_f
@_p.types(None,)
def glReleaseShaderCompiler():pass
@_f
@_p.types(None,_cs.GLsizei,arrays.GLuintArray,_cs.GLenum,ctypes.c_void_p,_cs.GLsizei)
def glShaderBinary(count,shaders,binaryFormat,binary,length):pass
