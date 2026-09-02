# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL.EGL the portable interface to GL environments"""
import ctypes as _ctypes
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLES1._types')
from OpenGL.GLES1.VERSION.GLES1_1_0 import *

glGetString.restype = _ctypes.c_char_p  # string return, cf. GL/glget.py
