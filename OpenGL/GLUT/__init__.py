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
