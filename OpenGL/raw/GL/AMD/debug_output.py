'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_AMD_debug_output'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_AMD_debug_output',error_checker=_errors._error_checker)
GL_DEBUG_CATEGORY_API_ERROR_AMD=_C('GL_DEBUG_CATEGORY_API_ERROR_AMD',0x9149)
GL_DEBUG_CATEGORY_APPLICATION_AMD=_C('GL_DEBUG_CATEGORY_APPLICATION_AMD',0x914F)
GL_DEBUG_CATEGORY_DEPRECATION_AMD=_C('GL_DEBUG_CATEGORY_DEPRECATION_AMD',0x914B)
GL_DEBUG_CATEGORY_OTHER_AMD=_C('GL_DEBUG_CATEGORY_OTHER_AMD',0x9150)
GL_DEBUG_CATEGORY_PERFORMANCE_AMD=_C('GL_DEBUG_CATEGORY_PERFORMANCE_AMD',0x914D)
GL_DEBUG_CATEGORY_SHADER_COMPILER_AMD=_C('GL_DEBUG_CATEGORY_SHADER_COMPILER_AMD',0x914E)
GL_DEBUG_CATEGORY_UNDEFINED_BEHAVIOR_AMD=_C('GL_DEBUG_CATEGORY_UNDEFINED_BEHAVIOR_AMD',0x914C)
GL_DEBUG_CATEGORY_WINDOW_SYSTEM_AMD=_C('GL_DEBUG_CATEGORY_WINDOW_SYSTEM_AMD',0x914A)
GL_DEBUG_LOGGED_MESSAGES_AMD=_C('GL_DEBUG_LOGGED_MESSAGES_AMD',0x9145)
GL_DEBUG_SEVERITY_HIGH_AMD=_C('GL_DEBUG_SEVERITY_HIGH_AMD',0x9146)
GL_DEBUG_SEVERITY_LOW_AMD=_C('GL_DEBUG_SEVERITY_LOW_AMD',0x9148)
GL_DEBUG_SEVERITY_MEDIUM_AMD=_C('GL_DEBUG_SEVERITY_MEDIUM_AMD',0x9147)
GL_MAX_DEBUG_LOGGED_MESSAGES_AMD=_C('GL_MAX_DEBUG_LOGGED_MESSAGES_AMD',0x9144)
GL_MAX_DEBUG_MESSAGE_LENGTH_AMD=_C('GL_MAX_DEBUG_MESSAGE_LENGTH_AMD',0x9143)
@_f
@_p.types(None,_cs.GLDEBUGPROCAMD,ctypes.c_void_p)
def glDebugMessageCallbackAMD(callback,userParam):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLsizei,arrays.GLuintArray,_cs.GLboolean)
def glDebugMessageEnableAMD(category,severity,count,ids,enabled):pass
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLuint,_cs.GLsizei,arrays.GLcharArray)
def glDebugMessageInsertAMD(category,severity,id,length,buf):pass
@_f
@_p.types(_cs.GLuint,_cs.GLuint,_cs.GLsizei,arrays.GLuintArray,arrays.GLuintArray,arrays.GLuintArray,arrays.GLsizeiArray,arrays.GLcharArray)
def glGetDebugMessageLogAMD(count,bufSize,categories,severities,ids,lengths,message):pass
