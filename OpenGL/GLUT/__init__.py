# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""The GLUT library implementation via ctypes"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.GLUT')

from OpenGL.GLUT.special import *
from OpenGL.GLUT.fonts import *
from OpenGL.GLUT.freeglut import *
from OpenGL.GLUT.osx import *

if glutLeaveMainLoop:
    HAVE_FREEGLUT = True 
else:
    HAVE_FREEGLUT = False 
