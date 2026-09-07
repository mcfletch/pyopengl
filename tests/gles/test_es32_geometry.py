#! /usr/bin/env python3
"""GLES3.2: geometry shader amplifying a point into a triangle.

Geometry shaders are core in ES3.2.  A single GL_POINTS vertex is expanded by
the geometry shader into a centred triangle, verified by pixel readback.
Skips where an ES3.2 context is unavailable.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_FLOAT,
    GL_FALSE,
    GL_POINTS,
    glUseProgram,
    glGenVertexArrays,
    glBindVertexArray,
    glGetAttribLocation,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
)
from OpenGL.GLES2.ES.VERSION_3_2 import GL_GEOMETRY_SHADER
from OpenGL.arrays.vbo import VBO

VERTEX_SHADER = '''#version 320 es
in vec2 position;
void main() {
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

GEOMETRY_SHADER = '''#version 320 es
layout(points) in;
layout(triangle_strip, max_vertices = 3) out;
void main() {
    gl_Position = vec4( -0.8, -0.8, 0.0, 1.0 ); EmitVertex();
    gl_Position = vec4(  0.8, -0.8, 0.0, 1.0 ); EmitVertex();
    gl_Position = vec4(  0.0,  0.8, 0.0, 1.0 ); EmitVertex();
    EndPrimitive();
}'''

FRAGMENT_SHADER = '''#version 320 es
precision mediump float;
out vec4 fragColor;
void main() {
    fragColor = vec4( 1.0, 1.0, 0.0, 1.0 );
}'''


class TestES32Geometry(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def test_geometry_amplification(self):
        program = self.compile_program(
            VERTEX_SHADER,
            FRAGMENT_SHADER,
            extra_stages=[(GL_GEOMETRY_SHADER, GEOMETRY_SHADER)],
        )
        glUseProgram(program)

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(vao))
        vbo = VBO(np.array([(0.0, 0.0)], dtype='f'))
        # The geometry shader emits fixed positions and never reads the vertex
        # output, so a conformant linker (NVIDIA) may drop the unused 'position'
        # attribute and return -1; only feed the attribute when it survives.
        position = glGetAttribLocation(program, 'position')
        with vbo:
            if position != -1:
                glEnableVertexAttribArray(position)
                glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 2 * 4, vbo)
            glDrawArrays(GL_POINTS, 0, 1)
        self.check_error('draw')

        cx, cy = self.width // 2, self.height // 2
        self.assert_pixel(cx, cy, (255, 255, 0, 255))
        self.assert_pixel(2, 2, (0, 0, 64, 255))


if __name__ == '__main__':
    unittest.main()
