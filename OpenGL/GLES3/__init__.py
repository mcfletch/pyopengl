"""OpenGL.EGL the portable interface to GL environments"""
import ctypes as _ctypes
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLES3._types')
from OpenGL.GLES2.VERSION.GLES2_2_0 import *
from OpenGL.GLES3.VERSION.GLES3_3_0 import *
from OpenGL.GLES3.VERSION.GLES3_3_1 import *

glGetString.restype = _ctypes.c_char_p  # string return, cf. GL/glget.py
glGetStringi.restype = _ctypes.c_char_p

from OpenGL.GLES2.images import (  # auto-alloc readback, size-checked uploads, table registration
    glReadPixels,
    glTexImage2D,
    glTexSubImage2D,
    glCompressedTexImage2D,
)
from OpenGL.GLES3.images import glTexImage3D, glTexSubImage3D  # size-checked 3D uploads
