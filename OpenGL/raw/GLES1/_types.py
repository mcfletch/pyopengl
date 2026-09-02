# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.raw.GL._types import *
from OpenGL.raw.GL import _types as _base
GLfixed = _base._defineType('GLfixed', ctypes.c_int32, int )
GLclampx = _base._defineType('GLclampx', ctypes.c_int32, int )
