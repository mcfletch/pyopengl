'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_VERSION_GL_3_2'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_VERSION_GL_3_2',error_checker=_errors._error_checker)
GL_ALREADY_SIGNALED=_C('GL_ALREADY_SIGNALED',0x911A)
GL_CONDITION_SATISFIED=_C('GL_CONDITION_SATISFIED',0x911C)
GL_CONTEXT_COMPATIBILITY_PROFILE_BIT=_C('GL_CONTEXT_COMPATIBILITY_PROFILE_BIT',0x00000002)
GL_CONTEXT_CORE_PROFILE_BIT=_C('GL_CONTEXT_CORE_PROFILE_BIT',0x00000001)
GL_CONTEXT_PROFILE_MASK=_C('GL_CONTEXT_PROFILE_MASK',0x9126)
GL_DEPTH_CLAMP=_C('GL_DEPTH_CLAMP',0x864F)
GL_FIRST_VERTEX_CONVENTION=_C('GL_FIRST_VERTEX_CONVENTION',0x8E4D)
GL_FRAMEBUFFER_ATTACHMENT_LAYERED=_C('GL_FRAMEBUFFER_ATTACHMENT_LAYERED',0x8DA7)
GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS=_C('GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS',0x8DA8)
GL_GEOMETRY_INPUT_TYPE=_C('GL_GEOMETRY_INPUT_TYPE',0x8917)
GL_GEOMETRY_OUTPUT_TYPE=_C('GL_GEOMETRY_OUTPUT_TYPE',0x8918)
GL_GEOMETRY_SHADER=_C('GL_GEOMETRY_SHADER',0x8DD9)
GL_GEOMETRY_VERTICES_OUT=_C('GL_GEOMETRY_VERTICES_OUT',0x8916)
GL_INT_SAMPLER_2D_MULTISAMPLE=_C('GL_INT_SAMPLER_2D_MULTISAMPLE',0x9109)
GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY=_C('GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY',0x910C)
GL_LAST_VERTEX_CONVENTION=_C('GL_LAST_VERTEX_CONVENTION',0x8E4E)
GL_LINES_ADJACENCY=_C('GL_LINES_ADJACENCY',0x000A)
GL_LINE_STRIP_ADJACENCY=_C('GL_LINE_STRIP_ADJACENCY',0x000B)
GL_MAX_COLOR_TEXTURE_SAMPLES=_C('GL_MAX_COLOR_TEXTURE_SAMPLES',0x910E)
GL_MAX_DEPTH_TEXTURE_SAMPLES=_C('GL_MAX_DEPTH_TEXTURE_SAMPLES',0x910F)
GL_MAX_FRAGMENT_INPUT_COMPONENTS=_C('GL_MAX_FRAGMENT_INPUT_COMPONENTS',0x9125)
GL_MAX_GEOMETRY_INPUT_COMPONENTS=_C('GL_MAX_GEOMETRY_INPUT_COMPONENTS',0x9123)
GL_MAX_GEOMETRY_OUTPUT_COMPONENTS=_C('GL_MAX_GEOMETRY_OUTPUT_COMPONENTS',0x9124)
GL_MAX_GEOMETRY_OUTPUT_VERTICES=_C('GL_MAX_GEOMETRY_OUTPUT_VERTICES',0x8DE0)
GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS=_C('GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS',0x8C29)
GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS=_C('GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS',0x8DE1)
GL_MAX_GEOMETRY_UNIFORM_COMPONENTS=_C('GL_MAX_GEOMETRY_UNIFORM_COMPONENTS',0x8DDF)
GL_MAX_INTEGER_SAMPLES=_C('GL_MAX_INTEGER_SAMPLES',0x9110)
GL_MAX_SAMPLE_MASK_WORDS=_C('GL_MAX_SAMPLE_MASK_WORDS',0x8E59)
GL_MAX_SERVER_WAIT_TIMEOUT=_C('GL_MAX_SERVER_WAIT_TIMEOUT',0x9111)
GL_MAX_VERTEX_OUTPUT_COMPONENTS=_C('GL_MAX_VERTEX_OUTPUT_COMPONENTS',0x9122)
GL_OBJECT_TYPE=_C('GL_OBJECT_TYPE',0x9112)
GL_PROGRAM_POINT_SIZE=_C('GL_PROGRAM_POINT_SIZE',0x8642)
GL_PROVOKING_VERTEX=_C('GL_PROVOKING_VERTEX',0x8E4F)
GL_PROXY_TEXTURE_2D_MULTISAMPLE=_C('GL_PROXY_TEXTURE_2D_MULTISAMPLE',0x9101)
GL_PROXY_TEXTURE_2D_MULTISAMPLE_ARRAY=_C('GL_PROXY_TEXTURE_2D_MULTISAMPLE_ARRAY',0x9103)
GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION=_C('GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION',0x8E4C)
GL_SAMPLER_2D_MULTISAMPLE=_C('GL_SAMPLER_2D_MULTISAMPLE',0x9108)
GL_SAMPLER_2D_MULTISAMPLE_ARRAY=_C('GL_SAMPLER_2D_MULTISAMPLE_ARRAY',0x910B)
GL_SAMPLE_MASK=_C('GL_SAMPLE_MASK',0x8E51)
GL_SAMPLE_MASK_VALUE=_C('GL_SAMPLE_MASK_VALUE',0x8E52)
GL_SAMPLE_POSITION=_C('GL_SAMPLE_POSITION',0x8E50)
GL_SIGNALED=_C('GL_SIGNALED',0x9119)
GL_SYNC_CONDITION=_C('GL_SYNC_CONDITION',0x9113)
GL_SYNC_FENCE=_C('GL_SYNC_FENCE',0x9116)
GL_SYNC_FLAGS=_C('GL_SYNC_FLAGS',0x9115)
GL_SYNC_FLUSH_COMMANDS_BIT=_C('GL_SYNC_FLUSH_COMMANDS_BIT',0x00000001)
GL_SYNC_GPU_COMMANDS_COMPLETE=_C('GL_SYNC_GPU_COMMANDS_COMPLETE',0x9117)
GL_SYNC_STATUS=_C('GL_SYNC_STATUS',0x9114)
GL_TEXTURE_2D_MULTISAMPLE=_C('GL_TEXTURE_2D_MULTISAMPLE',0x9100)
GL_TEXTURE_2D_MULTISAMPLE_ARRAY=_C('GL_TEXTURE_2D_MULTISAMPLE_ARRAY',0x9102)
GL_TEXTURE_BINDING_2D_MULTISAMPLE=_C('GL_TEXTURE_BINDING_2D_MULTISAMPLE',0x9104)
GL_TEXTURE_BINDING_2D_MULTISAMPLE_ARRAY=_C('GL_TEXTURE_BINDING_2D_MULTISAMPLE_ARRAY',0x9105)
GL_TEXTURE_CUBE_MAP_SEAMLESS=_C('GL_TEXTURE_CUBE_MAP_SEAMLESS',0x884F)
GL_TEXTURE_FIXED_SAMPLE_LOCATIONS=_C('GL_TEXTURE_FIXED_SAMPLE_LOCATIONS',0x9107)
GL_TEXTURE_SAMPLES=_C('GL_TEXTURE_SAMPLES',0x9106)
GL_TIMEOUT_EXPIRED=_C('GL_TIMEOUT_EXPIRED',0x911B)
GL_TIMEOUT_IGNORED=_C('GL_TIMEOUT_IGNORED',0xFFFFFFFFFFFFFFFF)
GL_TRIANGLES_ADJACENCY=_C('GL_TRIANGLES_ADJACENCY',0x000C)
GL_TRIANGLE_STRIP_ADJACENCY=_C('GL_TRIANGLE_STRIP_ADJACENCY',0x000D)
GL_UNSIGNALED=_C('GL_UNSIGNALED',0x9118)
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE=_C('GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE',0x910A)
GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY=_C('GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY',0x910D)
GL_WAIT_FAILED=_C('GL_WAIT_FAILED',0x911D)
@_f
@_p.types(_cs.GLenum,_cs.GLsync,_cs.GLbitfield,_cs.GLuint64)
def glClientWaitSync(sync,flags,timeout):pass
@_f
@_p.types(None,_cs.GLsync)
def glDeleteSync(sync):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLsizei,_cs.GLenum,ctypes.c_void_p,_cs.GLint)
def glDrawElementsBaseVertex(mode,count,type,indices,basevertex):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLsizei,_cs.GLenum,ctypes.c_void_p,_cs.GLsizei,_cs.GLint)
def glDrawElementsInstancedBaseVertex(mode,count,type,indices,instancecount,basevertex):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,_cs.GLuint,_cs.GLsizei,_cs.GLenum,ctypes.c_void_p,_cs.GLint)
def glDrawRangeElementsBaseVertex(mode,start,end,count,type,indices,basevertex):pass
@_f
@_p.types(_cs.GLsync,_cs.GLenum,_cs.GLbitfield)
def glFenceSync(condition,flags):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLuint,_cs.GLint)
def glFramebufferTexture(target,attachment,texture,level):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,arrays.GLint64Array)
def glGetBufferParameteri64v(target,pname,params):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,arrays.GLint64Array)
def glGetInteger64i_v(target,index,data):pass
@_f
@_p.types(None,_cs.GLenum,arrays.GLint64Array)
def glGetInteger64v(pname,data):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLuint,arrays.GLfloatArray)
def glGetMultisamplefv(pname,index,val):pass
@_f
@_p.types(None,_cs.GLsync,_cs.GLenum,_cs.GLsizei,arrays.GLsizeiArray,arrays.GLintArray)
def glGetSynciv(sync,pname,count,length,values):pass
@_f
@_p.types(_cs.GLboolean,_cs.GLsync)
def glIsSync(sync):pass
@_f
@_p.types(None,_cs.GLenum,arrays.GLsizeiArray,_cs.GLenum,arrays.GLvoidpArray,_cs.GLsizei,arrays.GLintArray)
def glMultiDrawElementsBaseVertex(mode,count,type,indices,drawcount,basevertex):pass
@_f
@_p.types(None,_cs.GLenum)
def glProvokingVertex(mode):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLbitfield)
def glSampleMaski(maskNumber,mask):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLsizei,_cs.GLenum,_cs.GLsizei,_cs.GLsizei,_cs.GLboolean)
def glTexImage2DMultisample(target,samples,internalformat,width,height,fixedsamplelocations):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLsizei,_cs.GLenum,_cs.GLsizei,_cs.GLsizei,_cs.GLsizei,_cs.GLboolean)
def glTexImage3DMultisample(target,samples,internalformat,width,height,depth,fixedsamplelocations):pass
@_f
@_p.types(None,_cs.GLsync,_cs.GLbitfield,_cs.GLuint64)
def glWaitSync(sync,flags,timeout):pass
