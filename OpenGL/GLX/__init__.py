# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""Platform-specific functions/support for the xorg/X11 windowing system"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLX._types')
from OpenGL.GLX.VERSION.GLX_1_0 import *
from OpenGL.GLX.VERSION.GLX_1_1 import *
from OpenGL.GLX.VERSION.GLX_1_2 import *
from OpenGL.GLX.VERSION.GLX_1_3 import *
from OpenGL.GLX.VERSION.GLX_1_4 import *
