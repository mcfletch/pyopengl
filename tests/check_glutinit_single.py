from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
glutInit([''])
glutInitDisplayMode (GLUT_SINGLE | GLUT_RGB)
try:
    if fgDeinitialize: fgDeinitialize(False)
except NameError as err:
    pass # Older PyOpenGL, you may see a seg-fault here...
