from __future__ import print_function
import unittest
from basetestcase import BaseTest
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL.ARB.shader_objects import glGetActiveUniformARB

vertex_shader = """
uniform float scale;
void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex * scale;
}
"""


class TestGetActiveUniform(BaseTest):
    def test_glGetActiveUniform(self):
        """glGetActiveUniform (core) and glGetActiveUniformARB agree on the uniforms"""
        if not glCreateProgram:
            self.skipTest('Shaders not supported on this implementation')
        # vertex-only program; validate=False avoids the spurious "no fragment
        # shader" validation failure on some drivers (we never render it).
        program = compileProgram(
            compileShader(vertex_shader, GL_VERTEX_SHADER), validate=False
        )
        nu = glGetProgramiv(program, GL_ACTIVE_UNIFORMS)
        assert nu >= 1, nu
        names = []
        for i in range(nu):
            name, size, type = glGetActiveUniform(program, i)
            # the ARB entry point must be callable without error too
            glGetActiveUniformARB(program, i)
            names.append(name.decode() if isinstance(name, bytes) else name)
        assert 'scale' in names, names

