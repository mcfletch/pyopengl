#! /usr/bin/env python
import egltest
import numpy
from OpenGL import GL

@egltest.egltest( api='opengl' )
def test_gl( ):
    GL.glClearColor( 1,0,0, 0 )
    GL.glClear( GL.GL_COLOR_BUFFER_BIT|GL.GL_DEPTH_BUFFER_BIT )

if __name__ == "__main__":
    test_gl()
    
