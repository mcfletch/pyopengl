"""The GLUT library implementation via ctypes"""
from OpenGL.raw.GLUT import *

from OpenGL.GLUT.special import *
from OpenGL.GLUT.fonts import *
try:
	from OpenGL.GLUT.freeglut import *
	HAVE_FREEGLUT = False
except ImportError, err:
	HAVE_FREEGLUT = True

# Bug on some Linux platforms does not allow error checking
# with GLUT functions which occur before the context has been
# created.  These lines turn off error checking for the functions 
# which are normally run before glutCreateWindow, note that 
# glutInit is already non-error-checking (from GLUT/special.py)
del glutInitDisplayMode.errcheck
del glutInitDisplayString.errcheck
del glutInitWindowPosition.errcheck
