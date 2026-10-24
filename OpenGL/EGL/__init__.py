# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""OpenGL.EGL, the portable interface to GL environments.

Every name here comes from an EGL library.  Importing the package raises
``ImportError`` when the platform has no EGL library, as on macOS, on Windows
without ANGLE, or on a machine with no graphics driver installed.  A program
can test for EGL by importing this package.
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
# The devices this system offers, and which of them rasterise on the CPU.
# Imported here so a caller can use ``EGL.devices.devices()`` after importing
# the package.  The module imports the three device extensions, which do no
# work until one is called.
from OpenGL.EGL import devices
