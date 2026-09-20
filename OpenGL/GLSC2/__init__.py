# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL SC 2.0, the safety-critical profile of OpenGL ES 2.0"""
import ctypes as _ctypes
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLSC2._types')
from OpenGL.GLSC2.SC.VERSION_2_0 import *

glGetString.restype = _ctypes.c_char_p  # string return, cf. GL/glget.py
