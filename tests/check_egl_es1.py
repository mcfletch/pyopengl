#! /usr/bin/env python
import egltest
import numpy
from OpenGL import GLES1 as GL

@egltest.egltest( api='gles1' )
def test_es1( ):
    GL.glClearColor( 1,0,0, 0 )
    GL.glClear( GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT )
    vertices = numpy.array( ( (1,0,0 ),(-1,0,0 ),(0,1,0 )), 'f')
    GL.glEnableClientState( GL.GL_VERTEX_ARRAY )
    GL.glVertexPointer( 3, GL.GL_FLOAT, 0, vertices )
    GL.glDrawArrays( GL.GL_TRIANGLES, 0, 3 )

if __name__ == "__main__":
    test_es1()
    
