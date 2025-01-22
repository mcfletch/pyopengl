'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_EXT_gpu_shader4'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_EXT_gpu_shader4',error_checker=_errors._error_checker)
GL_INT_SAMPLER_1D_ARRAY_EXT=_C('GL_INT_SAMPLER_1D_ARRAY_EXT',0x8DCE)
GL_INT_SAMPLER_1D_EXT=_C('GL_INT_SAMPLER_1D_EXT',0x8DC9)
GL_INT_SAMPLER_2D_ARRAY_EXT=_C('GL_INT_SAMPLER_2D_ARRAY_EXT',0x8DCF)
GL_INT_SAMPLER_2D_EXT=_C('GL_INT_SAMPLER_2D_EXT',0x8DCA)
GL_INT_SAMPLER_2D_RECT_EXT=_C('GL_INT_SAMPLER_2D_RECT_EXT',0x8DCD)
GL_INT_SAMPLER_3D_EXT=_C('GL_INT_SAMPLER_3D_EXT',0x8DCB)
GL_INT_SAMPLER_BUFFER_EXT=_C('GL_INT_SAMPLER_BUFFER_EXT',0x8DD0)
GL_INT_SAMPLER_CUBE_EXT=_C('GL_INT_SAMPLER_CUBE_EXT',0x8DCC)
GL_MAX_PROGRAM_TEXEL_OFFSET_EXT=_C('GL_MAX_PROGRAM_TEXEL_OFFSET_EXT',0x8905)
GL_MIN_PROGRAM_TEXEL_OFFSET_EXT=_C('GL_MIN_PROGRAM_TEXEL_OFFSET_EXT',0x8904)
GL_SAMPLER_1D_ARRAY_EXT=_C('GL_SAMPLER_1D_ARRAY_EXT',0x8DC0)
GL_SAMPLER_1D_ARRAY_SHADOW_EXT=_C('GL_SAMPLER_1D_ARRAY_SHADOW_EXT',0x8DC3)
GL_SAMPLER_2D_ARRAY_EXT=_C('GL_SAMPLER_2D_ARRAY_EXT',0x8DC1)
GL_SAMPLER_2D_ARRAY_SHADOW_EXT=_C('GL_SAMPLER_2D_ARRAY_SHADOW_EXT',0x8DC4)
GL_SAMPLER_BUFFER_EXT=_C('GL_SAMPLER_BUFFER_EXT',0x8DC2)
GL_SAMPLER_CUBE_SHADOW_EXT=_C('GL_SAMPLER_CUBE_SHADOW_EXT',0x8DC5)
GL_UNSIGNED_INT_SAMPLER_1D_ARRAY_EXT=_C('GL_UNSIGNED_INT_SAMPLER_1D_ARRAY_EXT',0x8DD6)
GL_UNSIGNED_INT_SAMPLER_1D_EXT=_C('GL_UNSIGNED_INT_SAMPLER_1D_EXT',0x8DD1)
GL_UNSIGNED_INT_SAMPLER_2D_ARRAY_EXT=_C('GL_UNSIGNED_INT_SAMPLER_2D_ARRAY_EXT',0x8DD7)
GL_UNSIGNED_INT_SAMPLER_2D_EXT=_C('GL_UNSIGNED_INT_SAMPLER_2D_EXT',0x8DD2)
GL_UNSIGNED_INT_SAMPLER_2D_RECT_EXT=_C('GL_UNSIGNED_INT_SAMPLER_2D_RECT_EXT',0x8DD5)
GL_UNSIGNED_INT_SAMPLER_3D_EXT=_C('GL_UNSIGNED_INT_SAMPLER_3D_EXT',0x8DD3)
GL_UNSIGNED_INT_SAMPLER_BUFFER_EXT=_C('GL_UNSIGNED_INT_SAMPLER_BUFFER_EXT',0x8DD8)
GL_UNSIGNED_INT_SAMPLER_CUBE_EXT=_C('GL_UNSIGNED_INT_SAMPLER_CUBE_EXT',0x8DD4)
GL_UNSIGNED_INT_VEC2_EXT=_C('GL_UNSIGNED_INT_VEC2_EXT',0x8DC6)
GL_UNSIGNED_INT_VEC3_EXT=_C('GL_UNSIGNED_INT_VEC3_EXT',0x8DC7)
GL_UNSIGNED_INT_VEC4_EXT=_C('GL_UNSIGNED_INT_VEC4_EXT',0x8DC8)
GL_VERTEX_ATTRIB_ARRAY_INTEGER_EXT=_C('GL_VERTEX_ATTRIB_ARRAY_INTEGER_EXT',0x88FD)
@_f
@_p.types(None,_cs.GLuint,_cs.GLuint,arrays.GLcharArray)
def glBindFragDataLocationEXT(program,color,name):pass
@_f
@_p.types(_cs.GLint,_cs.GLuint,arrays.GLcharArray)
def glGetFragDataLocationEXT(program,name):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint,arrays.GLuintArray)
def glGetUniformuivEXT(program,location,params):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLintArray)
def glGetVertexAttribIivEXT(index,pname,params):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLuintArray)
def glGetVertexAttribIuivEXT(index,pname,params):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLuint)
def glUniform1uiEXT(location,v0):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLsizei,arrays.GLuintArray)
def glUniform1uivEXT(location,count,value):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLuint,_cs.GLuint)
def glUniform2uiEXT(location,v0,v1):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLsizei,arrays.GLuintArray)
def glUniform2uivEXT(location,count,value):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLuint,_cs.GLuint,_cs.GLuint)
def glUniform3uiEXT(location,v0,v1,v2):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLsizei,arrays.GLuintArray)
def glUniform3uivEXT(location,count,value):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLuint,_cs.GLuint,_cs.GLuint,_cs.GLuint)
def glUniform4uiEXT(location,v0,v1,v2,v3):pass
@_f
@_p.types(None,_cs.GLint,_cs.GLsizei,arrays.GLuintArray)
def glUniform4uivEXT(location,count,value):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint)
def glVertexAttribI1iEXT(index,x):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLintArray)
def glVertexAttribI1ivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLuint)
def glVertexAttribI1uiEXT(index,x):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLuintArray)
def glVertexAttribI1uivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint,_cs.GLint)
def glVertexAttribI2iEXT(index,x,y):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLintArray)
def glVertexAttribI2ivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLuint,_cs.GLuint)
def glVertexAttribI2uiEXT(index,x,y):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLuintArray)
def glVertexAttribI2uivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint,_cs.GLint,_cs.GLint)
def glVertexAttribI3iEXT(index,x,y,z):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLintArray)
def glVertexAttribI3ivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLuint,_cs.GLuint,_cs.GLuint)
def glVertexAttribI3uiEXT(index,x,y,z):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLuintArray)
def glVertexAttribI3uivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLbyteArray)
def glVertexAttribI4bvEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint,_cs.GLint,_cs.GLint,_cs.GLint)
def glVertexAttribI4iEXT(index,x,y,z,w):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLintArray)
def glVertexAttribI4ivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLshortArray)
def glVertexAttribI4svEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLubyteArray)
def glVertexAttribI4ubvEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLuint,_cs.GLuint,_cs.GLuint,_cs.GLuint)
def glVertexAttribI4uiEXT(index,x,y,z,w):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLuintArray)
def glVertexAttribI4uivEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,arrays.GLushortArray)
def glVertexAttribI4usvEXT(index,v):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLint,_cs.GLenum,_cs.GLsizei,ctypes.c_void_p)
def glVertexAttribIPointerEXT(index,size,type,stride,pointer):pass
