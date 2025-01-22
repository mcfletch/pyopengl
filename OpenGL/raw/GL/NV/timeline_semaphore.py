'''Autogenerated by xml_generate script, do not edit!'''
from OpenGL import platform as _p, arrays
# Code generation uses this
from OpenGL.raw.GL import _types as _cs
# End users want this...
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _errors
from OpenGL.constant import Constant as _C

import ctypes
_EXTENSION_NAME = 'GL_NV_timeline_semaphore'
def _f( function ):
    return _p.createFunction( function,_p.PLATFORM.GL,'GL_NV_timeline_semaphore',error_checker=_errors._error_checker)
GL_MAX_TIMELINE_SEMAPHORE_VALUE_DIFFERENCE_NV=_C('GL_MAX_TIMELINE_SEMAPHORE_VALUE_DIFFERENCE_NV',0x95B6)
GL_SEMAPHORE_TYPE_BINARY_NV=_C('GL_SEMAPHORE_TYPE_BINARY_NV',0x95B4)
GL_SEMAPHORE_TYPE_NV=_C('GL_SEMAPHORE_TYPE_NV',0x95B3)
GL_SEMAPHORE_TYPE_TIMELINE_NV=_C('GL_SEMAPHORE_TYPE_TIMELINE_NV',0x95B5)
GL_TIMELINE_SEMAPHORE_VALUE_NV=_C('GL_TIMELINE_SEMAPHORE_VALUE_NV',0x9595)
@_f
@_p.types(None,_cs.GLsizei,arrays.GLuintArray)
def glCreateSemaphoresNV(n,semaphores):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLintArray)
def glGetSemaphoreParameterivNV(semaphore,pname,params):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLintArray)
def glSemaphoreParameterivNV(semaphore,pname,params):pass
