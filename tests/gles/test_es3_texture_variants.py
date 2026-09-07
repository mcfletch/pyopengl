#! /usr/bin/env python3
"""GLES3.0: texture upload variants -- glTexSubImage2D, glTexImage3D, mipmaps.

Verifies the input image entry points (which forward numpy data) actually round
-trip through real draws:

* a 2D texture patched with glTexSubImage2D then glGenerateMipmap, and
* a 3D texture uploaded with glTexImage3D and sampled at a chosen layer.
"""

import unittest
import pytest
np = pytest.importorskip('numpy')  # numpy-specific test: skip without numpy

from arraycompat import one
from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLE_STRIP,
    GL_TEXTURE_2D,
    GL_TEXTURE_3D,
    GL_TEXTURE0,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TEXTURE_WRAP_R,
    GL_NEAREST,
    GL_CLAMP_TO_EDGE,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    glUseProgram,
    glGenTextures,
    glBindTexture,
    glActiveTexture,
    glTexParameteri,
    glTexImage2D,
    glTexSubImage2D,
    glTexImage3D,
    glTexSubImage3D,
    glGenerateMipmap,
    glGetAttribLocation,
    glGetUniformLocation,
    glUniform1i,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
)
from OpenGL.arrays.vbo import VBO

# full-screen triangle strip: position.xy, texcoord.uv
QUAD = np.array(
    [
        (-1.0, -1.0, 0.0, 0.0),
        (1.0, -1.0, 1.0, 0.0),
        (-1.0, 1.0, 0.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
    ],
    dtype='f',
)

VERTEX_SHADER = '''#version 300 es
in vec2 position;
in vec2 texcoord;
out vec2 vtex;
void main() {
    vtex = texcoord;
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

FRAGMENT_2D = '''#version 300 es
precision mediump float;
in vec2 vtex;
uniform sampler2D tex;
out vec4 fragColor;
void main() { fragColor = texture( tex, vtex ); }'''

FRAGMENT_3D = '''#version 300 es
precision mediump float;
in vec2 vtex;
uniform mediump sampler3D tex;
out vec4 fragColor;
void main() { fragColor = texture( tex, vec3( vtex, 0.25 ) ); }'''

BLUE = (0, 0, 255, 255)
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 255)


class TestES3TextureVariants(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def _draw_quad(self, program):
        glUseProgram(program)
        vbo = VBO(QUAD)
        position = glGetAttribLocation(program, 'position')
        texcoord = glGetAttribLocation(program, 'texcoord')
        with vbo:
            glEnableVertexAttribArray(position)
            glEnableVertexAttribArray(texcoord)
            glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 16, vbo)
            glVertexAttribPointer(texcoord, 2, GL_FLOAT, GL_FALSE, 16, vbo + 8)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    def _nearest_clamp(self, target, wraps):
        glTexParameteri(target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        for wrap in wraps:
            glTexParameteri(target, wrap, GL_CLAMP_TO_EDGE)

    def test_subimage_and_mipmap(self):
        program = self.compile_program(VERTEX_SHADER, FRAGMENT_2D)
        texture = one(glGenTextures(1))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        self._nearest_clamp(GL_TEXTURE_2D, (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T))

        base = np.tile(np.array(BLUE, np.uint8), (2, 2, 1))
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, base
        )
        # patch the bottom-left texel (origin) to red
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            1,
            1,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.array([[RED]], np.uint8),
        )
        glGenerateMipmap(GL_TEXTURE_2D)
        self.check_error('2d upload')

        glUseProgram(program)
        glUniform1i(glGetUniformLocation(program, 'tex'), 0)
        self._draw_quad(program)
        self.check_error('2d draw')

        qx, qy = self.width // 4, self.height // 4
        self.assert_pixel(qx, qy, RED)  # bottom-left: patched texel
        self.assert_pixel(3 * qx, 3 * qy, BLUE)  # top-right: untouched

    def test_3d_texture(self):
        program = self.compile_program(VERTEX_SHADER, FRAGMENT_3D)
        texture = one(glGenTextures(1))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_3D, texture)
        self._nearest_clamp(
            GL_TEXTURE_3D, (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R)
        )

        # shape (depth, height, width, 4); layer 0 green, layer 1 red
        volume = np.zeros((2, 2, 2, 4), np.uint8)
        volume[0] = GREEN
        volume[1] = RED
        glTexImage3D(
            GL_TEXTURE_3D, 0, GL_RGBA, 2, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, volume
        )
        self.check_error('3d upload')

        glUseProgram(program)
        glUniform1i(glGetUniformLocation(program, 'tex'), 0)
        self._draw_quad(program)
        self.check_error('3d draw')

        # shader samples w=0.25 -> layer 0 (green)
        self.assert_pixel(self.width // 2, self.height // 2, GREEN)

    def test_undersized_3d_upload_raises(self):
        """A 3D array too small for the declared volume is rejected."""
        texture = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_3D, texture)
        too_small = np.zeros((2, 2, 2, 4), np.uint8)  # 32 bytes; 4x4x4 needs 256
        with self.assertRaises(ValueError):
            glTexImage3D(
                GL_TEXTURE_3D,
                0,
                GL_RGBA,
                4,
                4,
                4,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                too_small,
            )
        with self.assertRaises(ValueError):
            glTexSubImage3D(
                GL_TEXTURE_3D,
                0,
                0,
                0,
                0,
                2,
                2,
                2,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                np.zeros((1, 1, 1, 4), np.uint8),
            )


if __name__ == '__main__':
    unittest.main()
