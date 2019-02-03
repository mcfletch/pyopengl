#! /usr/bin/env python
from __future__ import print_function
import egltest
from numpy import array
from OpenGL.arrays.vbo import VBO
from OpenGL.arrays import ArrayDatatype
from OpenGL.GLES2 import *
from OpenGL.GLES2 import shaders

@egltest.egltest( api='es2' )
def test_gl( ):
    glClearColor( 1,0,0, 0 )
    glClear( GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT )
    
    print('Error before compilation?', glGetError())
    shader = shaders.compileProgram(
        shaders.compileShader( '''#version 130
    attribute vec3 position;
    void main() {
        gl_Position = vec4( position, 0 );
    }''', GL_VERTEX_SHADER),
        shaders.compileShader( '''#version 130
    void main() {
        gl_FragColor = vec4( 0,1,0,.5 );
    }''', GL_FRAGMENT_SHADER),
    )
    vbo = VBO( array([
        (0,1,0),
        (1,-1,0),
        (-1,-1,0),
    ],dtype='f'))
    position_location = glGetAttribLocation(
        shader, 'position'
    )
    stride = 3*4
    with vbo:
        with shader:
            glEnableVertexAttribArray( position_location )
            stride = 3*4
            glVertexAttribPointer(
                position_location,
                3, GL_FLOAT,False, stride, vbo
            )
            glDrawArrays( GL_TRIANGLES, 0, 3 )

    
if __name__ == "__main__":
    test_gl()
    
