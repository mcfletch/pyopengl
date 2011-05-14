#! /usr/bin/env python
"""Tests initializing a GLUT 3.x context (freeglut extension apis)"""
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time

resX,resY = (400,300 )

def display( ):
    glutSetWindow(window);
    glClearColor (0.0, 0.0, (time.time()%1.0)/1.0, 0.0)
    glClear (GL_COLOR_BUFFER_BIT)
    glFlush ()
    glutSwapBuffers()


if __name__ == "__main__":
    glutInit([])
    glutInitContextVersion(3, 2)
    glutInitContextFlags(GLUT_FORWARD_COMPATIBLE)
    glutInitContextProfile(GLUT_CORE_PROFILE)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowSize(resX, resY)

    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("hello")
    glutDisplayFunc(display)
    glutMainLoop()
    
