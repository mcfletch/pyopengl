import sys, pygame
from math import sin
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import *
from OpenGL.GL.ARB.shader_objects import glGetActiveUniformARB

vertex_shader = """
uniform float scale;
void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex * scale;
}
"""

pygame.init()
disp = pygame.display.set_mode((1024, 768), OPENGL | DOUBLEBUF)

program = compileProgram(
    compileShader( vertex_shader, GL_VERTEX_SHADER )
)

nu = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
for i in range(nu):
    name, size, type = glGetActiveUniform(program, i)
    print 'CORE - ', name, size, type
    glGetActiveUniformARB( program, i )
    print 'ARB  - ', name, size, type
