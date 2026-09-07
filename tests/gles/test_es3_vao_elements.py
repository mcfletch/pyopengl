#! /usr/bin/env python3
"""GLES3.0: VAO, indexed drawing (glDrawElements) and glGetStringi.

Exercises ES3-core features: a vertex array object, an element buffer drawn
with 32-bit indices, a ``#version 300 es`` shader, and the indexed extension
query.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_VERSION,
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_ELEMENT_ARRAY_BUFFER,
    glUseProgram,
    glGenVertexArrays,
    glBindVertexArray,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawElements,
)
from OpenGL.arrays.vbo import VBO

VERTEX_SHADER = '''#version 300 es
layout(location = 0) in vec2 position;
void main() {
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

FRAGMENT_SHADER = '''#version 300 es
precision mediump float;
out vec4 fragColor;
void main() {
    fragColor = vec4( 0.0, 1.0, 0.0, 1.0 );
}'''


class TestES3VAOElements(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_indexed_quad(self):
        version = self.getString(GL_VERSION)
        self.assertIn('OpenGL ES 3', version)
        self.assertTrue(self.extensions(), 'glGetStringi returned no extensions')

        program = self.compile_program(VERTEX_SHADER, FRAGMENT_SHADER)
        glUseProgram(program)

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(vao))

        vertices = VBO(
            np.array(
                [(-0.8, -0.8), (0.8, -0.8), (0.8, 0.8), (-0.8, 0.8)],
                dtype='f',
            )
        )
        indices = VBO(
            np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32),
            target=GL_ELEMENT_ARRAY_BUFFER,
        )
        with vertices, indices:
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * 4, vertices)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        self.check_error('draw')

        cx, cy = self.width // 2, self.height // 2
        self.assert_pixel(cx, cy, (0, 255, 0, 255))
        self.assert_pixel(2, 2, (0, 0, 64, 255))


if __name__ == '__main__':
    unittest.main()
