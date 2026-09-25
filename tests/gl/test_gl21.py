#! /usr/bin/env python3
"""GL 2.1: non-square uniform matrices."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *

VERTEX = '''#version 120
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
void main() {
    float s = m23[0][0]+m32[0][0]+m24[0][0]+m42[0][0]+m34[0][0]+m43[0][0];
    gl_Position = gl_Vertex * s;
}'''
FRAGMENT = '''#version 120
void main() { gl_FragColor = vec4(1.0); }'''


class TestGL21(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_nonsquare_matrices(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        def loc(n):
            return glGetUniformLocation(program, n)
        glUniformMatrix2x3fv(loc('m23'), 1, False, np.zeros((2, 3), 'f'))
        glUniformMatrix3x2fv(loc('m32'), 1, False, np.zeros((3, 2), 'f'))
        glUniformMatrix2x4fv(loc('m24'), 1, False, np.zeros((2, 4), 'f'))
        glUniformMatrix4x2fv(loc('m42'), 1, False, np.zeros((4, 2), 'f'))
        glUniformMatrix3x4fv(loc('m34'), 1, False, np.zeros((3, 4), 'f'))
        glUniformMatrix4x3fv(loc('m43'), 1, False, np.zeros((4, 3), 'f'))
        self.check_error('non-square matrices')


if __name__ == '__main__':
    unittest.main()
