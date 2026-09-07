#! /usr/bin/env python3
"""GLES3.0: compressed texture upload via glCompressedTexImage2D (ETC2).

ETC2 is core in ES3.  A single all-zero ETC2 RGB8 block decodes to a uniform
dark grey on a conformant decoder; we upload it, draw a textured quad and
confirm the result is uniform, grey and distinct from the clear colour -- i.e.
the compressed data was decoded and sampled.  (The exact decoded value is
decoder-defined, so it is not hard-coded.)
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLE_STRIP,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_NEAREST,
    GL_COMPRESSED_RGB8_ETC2,
    glUseProgram,
    glGenTextures,
    glBindTexture,
    glActiveTexture,
    glTexParameteri,
    glCompressedTexImage2D,
    glCompressedTexSubImage2D,
    glGetAttribLocation,
    glGetUniformLocation,
    glUniform1i,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArrays,
)
from OpenGL.arrays.vbo import VBO

VERTEX_SHADER = '''#version 300 es
in vec2 position;
in vec2 texcoord;
out vec2 vtex;
void main() {
    vtex = texcoord;
    gl_Position = vec4( position, 0.0, 1.0 );
}'''

FRAGMENT_SHADER = '''#version 300 es
precision mediump float;
in vec2 vtex;
uniform sampler2D tex;
out vec4 fragColor;
void main() { fragColor = texture( tex, vtex ); }'''

# one 4x4 ETC2 RGB8 block (8 bytes); all-zero -> uniform dark grey
ETC2_BLOCK = np.zeros(8, np.uint8)


class TestES3CompressedTexture(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_compressed_upload(self):
        program = self.compile_program(VERTEX_SHADER, FRAGMENT_SHADER)
        texture = one(glGenTextures(1))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glCompressedTexImage2D(
            GL_TEXTURE_2D, 0, GL_COMPRESSED_RGB8_ETC2, 4, 4, 0, 8, ETC2_BLOCK
        )
        # patch the same block in place to exercise the sub-image path
        glCompressedTexSubImage2D(
            GL_TEXTURE_2D, 0, 0, 0, 4, 4, GL_COMPRESSED_RGB8_ETC2, 8, ETC2_BLOCK
        )
        self.check_error('compressed upload')

        glUseProgram(program)
        glUniform1i(glGetUniformLocation(program, 'tex'), 0)
        vbo = VBO(
            np.array(
                [(-1, -1, 0, 0), (1, -1, 1, 0), (-1, 1, 0, 1), (1, 1, 1, 1)],
                dtype='f',
            )
        )
        position = glGetAttribLocation(program, 'position')
        texcoord = glGetAttribLocation(program, 'texcoord')
        with vbo:
            glEnableVertexAttribArray(position)
            glEnableVertexAttribArray(texcoord)
            glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 16, vbo)
            glVertexAttribPointer(texcoord, 2, GL_FLOAT, GL_FALSE, 16, vbo + 8)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        self.check_error('draw')

        image = self.read_image()
        qx, qy = self.width // 4, self.height // 4
        # chained indexing works for both numpy and the ctypes fallback
        samples = [
            tuple(int(c) for c in image[int(y)][int(x)])
            for y in (qy, 3 * qy)
            for x in (qx, 3 * qx)
        ]
        first = samples[0]
        for s in samples[1:]:
            self.assertEqual(
                s, first, 'compressed texture not uniform: %r' % (samples,)
            )
        r, g, b, a = first
        self.assertTrue(abs(r - g) <= 4 and abs(g - b) <= 4, 'not grey: %r' % (first,))
        self.assertNotEqual((r, g, b), (0, 0, 64), 'texture not applied (still clear)')


if __name__ == '__main__':
    unittest.main()
