#! /usr/bin/env python
"""This script is intended to give me an idea of current performance with various drawing strategies"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
import cProfile, time, os
PROFILER = cProfile.Profile()

import numpy

def dump( ):
    def newfile( base ):
        new = base 
        count = 0
        while os.path.isfile( new ):
            new = '%s-%s%s'%( 
                os.path.splitext(base)[0], 
                count,
                os.path.splitext(base)[1] 
            )
            count += 1
        return new
    PROFILER.dump_stats( newfile( 'performance.profile' ) )


def init_vbo( size = 1000000 ):
    """Create VBO with vertices of count size"""
    a = numpy.zeros( (size,3), dtype='d')
    xes = numpy.arange(-5,5,float(10)/size, dtype='d' )
    a[:len(xes),0] = xes
    a[:len(xes),1] = numpy.sin( xes )
    a[:len(xes),2] = numpy.cos( xes )
    v = a
    v = vbo.VBO( a )
    v.bind()
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnable( GL_LIGHTING )
    glEnable( GL_LIGHT0 )
    glDisable( GL_CULL_FACE )
    glColor3f( 1.0,1.0,1.0)
    glNormal3f( 0.0, 0.0, 1.0 )
    return v 

def draw_with_array( a , count):
    glDrawArrays( GL_TRIANGLES, 0, (count) )
    glFlush()
    glutSwapBuffers()

def init():
    glMatrixMode (GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(40.0, 300/300, 1.0, 20.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(
        20,0,0, # eyepoint
        0,0,0, # center-of-view
        0,1,0, # up-vector
    )
    glClearColor( 0,0,.25, 0 )
    glClear( GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT )

def display( ):
    init()
    repeat = range(100)
    for count in [(2**i) for i in range(8,19)]:
        v = init_vbo( count )
        def x( ):
            t1 = time.time()
            for i in repeat:
                glVertexPointer(  3, GL_DOUBLE, 0, v )
                draw_with_array( v, count )
            t2 = time.time()
            print 'Count: %s Total Time for %s iterations: %s  MTri/s: %s'%(
                count, len(repeat), t2-t1, (count*len(repeat)/(t2-t1)/1000000)
            )
        PROFILER.runcall( x )
    dump()
    import sys
    sys.exit(1)
    print 'should not get here'

if __name__ == "__main__":
    import sys
    newArgv = glutInit(sys.argv)
    glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
    glutInitWindowSize(250, 250)
    glutInitWindowPosition(100, 100)
    window = glutCreateWindow("hello")
    glutDisplayFunc(display)
    glutMainLoop()