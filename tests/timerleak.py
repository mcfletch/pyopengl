#! /usr/bin/env python
from OpenGL.GLUT import *

delay = 1
count = 0

def timerCallback(value):
    global count
    count += 1
    if count % 2000 == 0: print count
    glutTimerFunc( delay, timerCallback, value+1 )

if __name__ == "__main__":
    glutInit( sys.argv )
    glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH )
    glutInitWindowSize( 100, 100 )
    glutCreateWindow( "testtimer" )

    glutTimerFunc( delay, timerCallback, 0 )

    glutMainLoop()