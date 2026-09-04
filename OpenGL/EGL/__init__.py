# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL.EGL the portable interface to GL environments

Every name here is one in an EGL library, so importing the package raises
``ImportError`` where the platform has no EGL to load -- macOS, a Windows
without ANGLE, a machine with no graphics driver installed. That import is
therefore how a program asks whether this machine has EGL at all.
"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.EGL._types')
from OpenGL.raw.EGL._errors import EGLError
from OpenGL.EGL.VERSION.EGL_1_0 import *
from OpenGL.EGL.VERSION.EGL_1_1 import *
from OpenGL.EGL.VERSION.EGL_1_2 import *
from OpenGL.EGL.VERSION.EGL_1_3 import *
from OpenGL.EGL.VERSION.EGL_1_4 import *
from OpenGL.EGL.VERSION.EGL_1_5 import *
# Which devices this system offers, and which of them rasterise on the CPU.
# Bound here so that a caller who has imported the package can reach it as
# ``EGL.devices.devices()``; the module's own imports are the three device
# extensions, which cost nothing until one is called.
from OpenGL.EGL import devices
