#! /usr/bin/env python3
"""Smoke tests: core-profile shader render and compatibility immediate-mode."""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import (
    GL_VERSION,
    GL_VENDOR,
    GL_RENDERER,
    GL_SHADING_LANGUAGE_VERSION,
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_COLOR_BUFFER_BIT,
    glUseProgram,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    glGetAttribLocation,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
    glBegin,
    glEnd,
    glColor3f,
    glVertex2f,
    glClear,
)

CORE_VS = '''#version 330 core
layout(location=0) in vec2 position;
void main() { gl_Position = vec4(position, 0.0, 1.0); }'''
CORE_FS = '''#version 330 core
out vec4 fragColor;
void main() { fragColor = vec4(1.0, 0.5, 0.0, 1.0); }'''


class TestCoreSmoke(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_introspection(self):
        self.assertTrue(self.getString(GL_VERSION))
        # Profile is verified portably via GL_CONTEXT_PROFILE_MASK; only Mesa
        # spells the profile out in GL_VERSION (NVIDIA reports "3.3.0 NVIDIA").
        self.assert_profile('core')
        for enum in (GL_VENDOR, GL_RENDERER, GL_SHADING_LANGUAGE_VERSION):
            self.assertTrue(self.getString(enum))
        self.check_error('introspection')

    def test_triangle(self):
        program = self.compile_program(CORE_VS, CORE_FS)
        glUseProgram(program)
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            np.array([(0, 0.8), (-0.8, -0.8), (0.8, -0.8)], 'f'),
            GL_STATIC_DRAW,
        )
        loc = glGetAttribLocation(program, 'position')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 2, GL_FLOAT, GL_FALSE, 0, None)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        self.check_error('draw')
        self.assert_pixel(self.width // 2, self.height // 2, (255, 128, 0, 255))
        self.assert_pixel(2, 2, (0, 0, 64, 255))


class TestCompatSmoke(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_immediate_mode(self):
        # Verify the profile portably (NVIDIA's GL_VERSION omits "Compatibility");
        # the immediate-mode draw below is the real proof the profile works.
        self.assert_profile('compatibility')
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(0.0, 0.8)
        glVertex2f(-0.8, -0.8)
        glVertex2f(0.8, -0.8)
        glEnd()
        self.check_error('immediate mode')
        self.assert_pixel(self.width // 2, self.height // 2, (0, 255, 0, 255))


if __name__ == '__main__':
    unittest.main()
