# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""The GLUT library implementation via ctypes"""
from OpenGL.extensions import available
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLUT')

from OpenGL.GLUT.special import *
from OpenGL.GLUT.fonts import *
from OpenGL.GLUT.freeglut import *
from OpenGL.GLUT.osx import *

#: freeglut's own entry points are absent from the original GLUT, so whether
#: one resolves is what says which library this is.
HAVE_FREEGLUT = available(glutLeaveMainLoop) 
