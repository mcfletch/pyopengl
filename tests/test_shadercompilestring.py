from pygamegltest import gltest
import OpenGL
from OpenGL import GL
import time

SAMPLE_SHADER = '''#version 330
void main() { gl_Position = vec4(0,0,0,0);}'''

@gltest 
def test_compile_string( ):
    shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)

    GL.glShaderSource(shader, SAMPLE_SHADER)
    GL.glCompileShader(shader)
    if not bool(GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)) == True:
        print('Info log:')
        print(GL.glGetShaderInfoLog(shader))
        assert False, """Failed to compile"""
    
