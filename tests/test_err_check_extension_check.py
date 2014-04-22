import OpenGL
OpenGL.ERROR_CHECKING = False
OpenGL.USE_ACCELERATE = False

from OpenGL.GLUT import *

def reshape(width, height): pass
def display(): glutSwapBuffers()

def main():
    glutInit([])
    glutInitDisplayMode(GLUT_RGBA|GLUT_3_2_CORE_PROFILE)
    glutCreateWindow(b"test")
    glutReshapeFunc(reshape)
    glutDisplayFunc(display)

    from OpenGL.GL import glGenVertexArrays, glVertex3f
    assert bool(glGenVertexArrays)
    try:
        if fgDeinitialize: fgDeinitialize(False)
    except NameError as err:
        pass # Older PyOpenGL, you may see a seg-fault here...

if __name__ == "__main__":
    main()
