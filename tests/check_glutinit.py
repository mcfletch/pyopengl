# requires: glut
from __future__ import print_function
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import os, time, sys

resX, resY = (400, 300)


def display():
    glutSetWindow(window)
    glClearColor(0.0, 0.0, (time.time() % 1.0) / 1.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glFlush()
    glutSwapBuffers()
    sys.stdout.write('OK\n')
    sys.stdout.flush()
    if glutLeaveMainLoop:
        glutLeaveMainLoop()
    else:
        # Classic GLUT -- macOS's -- has no way out of glutMainLoop; that gap
        # is why freeglut added glutLeaveMainLoop.  Everything this check set
        # out to do is done and printed by here, so end the process rather than
        # spin in the loop until the harness times the script out.
        os._exit(0)


if __name__ == "__main__":
    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowSize(resX, resY)

    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("hello")
    glutDisplayFunc(display)
    for name in (GL_VENDOR, GL_RENDERER, GL_SHADING_LANGUAGE_VERSION, GL_EXTENSIONS):
        print(('%s = %r' % (name, glGetString(name))))

    glutMainLoop()
