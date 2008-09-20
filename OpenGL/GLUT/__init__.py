"""The GLUT library implementation via ctypes"""
from OpenGL.raw.GLUT import *

from OpenGL.GLUT.special import *
from OpenGL.GLUT.fonts import *
try:
	from OpenGL.GLUT.freeglut import *
	HAVE_FREEGLUT = False
except ImportError, err:
	HAVE_FREEGLUT = True

