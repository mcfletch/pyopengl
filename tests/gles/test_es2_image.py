#! /usr/bin/env python3
"""GLES2: image handling -- texture upload from a numpy array and readback.

Uploads a 2x2 RGBA texture with glTexImage2D, draws a full-screen textured
quad with nearest filtering (so each screen quadrant shows one texel), then
reads the whole framebuffer back with the auto-allocating glReadPixels and
checks each quadrant against the source texels.
"""

import unittest
from arraycompat import np, one, shape  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES2 import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLE_STRIP,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
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
    glGetAttribLocation,
    glGetUniformLocation,
    glUniform1i,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
)
from OpenGL.arrays.vbo import VBO

VERTEX_SHADER = '''#version 100
attribute vec2 position;
attribute vec2 texcoord;
varying vec2 vtex;
void main() {
    vtex = texcoord;
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

FRAGMENT_SHADER = '''#version 100
precision mediump float;
varying vec2 vtex;
uniform sampler2D tex;
void main() {
    gl_FragColor = texture2D( tex, vtex );
}'''

# Texel layout: row 0 is the bottom (GL texcoord t=0).
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 255)
BLUE = (0, 0, 255, 255)
YELLOW = (255, 255, 0, 255)
TEXELS = np.array([[RED, GREEN], [BLUE, YELLOW]], dtype=np.uint8)


class TestES2Image(ESTestCase):
    api = 'gles'
    gl_version = (2, 0)

    def test_texture_roundtrip(self):
        program = self.compile_program(VERTEX_SHADER, FRAGMENT_SHADER)
        glUseProgram(program)

        texture = one(glGenTextures(1))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        for pname in (GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER):
            glTexParameteri(GL_TEXTURE_2D, pname, GL_NEAREST)
        for pname in (GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T):
            glTexParameteri(GL_TEXTURE_2D, pname, GL_CLAMP_TO_EDGE)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, 2, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, TEXELS
        )
        glUniform1i(glGetUniformLocation(program, 'tex'), 0)
        self.check_error('texture upload')

        # interleaved position.xy, texcoord.uv for a full-screen triangle strip
        quad = VBO(
            np.array(
                [
                    (-1.0, -1.0, 0.0, 0.0),
                    (1.0, -1.0, 1.0, 0.0),
                    (-1.0, 1.0, 0.0, 1.0),
                    (1.0, 1.0, 1.0, 1.0),
                ],
                dtype='f',
            )
        )
        position = glGetAttribLocation(program, 'position')
        texcoord = glGetAttribLocation(program, 'texcoord')
        stride = 4 * 4
        with quad:
            glEnableVertexAttribArray(position)
            glEnableVertexAttribArray(texcoord)
            glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, stride, quad)
            glVertexAttribPointer(texcoord, 2, GL_FLOAT, GL_FALSE, stride, quad + 8)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        self.check_error('draw')

        image = self.read_image()
        self.assertEqual(shape(image), (self.height, self.width, 4))
        qx, qy = self.width // 4, self.height // 4
        # image is indexed [y][x]; y grows upward from the bottom-left origin
        # (chained indexing works for both numpy and the ctypes fallback)
        corners = {
            'bottom-left': (image[qy][qx], RED),
            'bottom-right': (image[qy][3 * qx], GREEN),
            'top-left': (image[3 * qy][qx], BLUE),
            'top-right': (image[3 * qy][3 * qx], YELLOW),
        }
        for name, (actual, expected) in corners.items():
            self.assertEqual(
                tuple(actual),
                expected,
                '%s quadrant: %r != %r' % (name, tuple(actual), expected),
            )

    def test_undersized_upload_raises(self):
        """An array too small for the declared dimensions is rejected."""
        texture = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture)
        too_small = np.zeros((2, 2, 4), np.uint8)  # 16 bytes; an 8x8 image needs 256
        with self.assertRaises(ValueError):
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGBA, 8, 8, 0, GL_RGBA, GL_UNSIGNED_BYTE, too_small
            )


if __name__ == '__main__':
    unittest.main()
