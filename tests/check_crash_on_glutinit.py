from OpenGL.GLUT import *
from OpenGL.GL import *


def main():
    if glutInit:
        glutInit(' ')
        glutInitDisplayMode(GLUT_SINGLE)
        window = glutCreateWindow("hello")
        glutDisplayFunc(lambda *args: 1)
        # glutMainLoop()
        try:
            if fgDeinitialize:
                fgDeinitialize(False)
        except NameError as err:
            pass  # Older PyOpenGL, you may see a seg-fault here...
        print('OK')
    else:
        print('SKIP')


if __name__ == "__main__":
    main()
