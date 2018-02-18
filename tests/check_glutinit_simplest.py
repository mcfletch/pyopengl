from OpenGL.GLUT import *
glutInit()
glutInitDisplayMode(GLUT_RGB)
try:
    if fgDeinitialize: fgDeinitialize(False)
except NameError as err:
    pass # Older PyOpenGL, you may see a seg-fault here...
