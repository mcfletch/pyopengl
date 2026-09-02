# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL.EGL the portable interface to GL environments"""
import ctypes as _ctypes
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLES2._types')
from OpenGL.GLES2.VERSION.GLES2_2_0 import *

from OpenGL.GLES2 import vboimplementation as _gles2_implementation

glGetString.restype = _ctypes.c_char_p  # string return, cf. GL/glget.py

from OpenGL.GLES2.images import (  # auto-alloc readback, size-checked uploads, table registration
    glReadPixels,
    glTexImage2D,
    glTexSubImage2D,
    glCompressedTexImage2D,
)
