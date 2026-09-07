#! /usr/bin/env python3
"""GLES3.2: texture buffers, integer texture/sampler params, multisample-array
storage and the KHR_robustness sized queries."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_R32UI,
    GL_RGBA8,
    GL_TEXTURE_2D,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_NO_ERROR,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glGenTextures,
    glBindTexture,
    glGenSamplers,
    glDeleteSamplers,
    glUseProgram,
    glGetUniformLocation,
)
from OpenGL.GLES2.ES.VERSION_3_2 import (
    GL_TEXTURE_BUFFER,
    GL_TEXTURE_BORDER_COLOR,
    GL_TEXTURE_2D_MULTISAMPLE_ARRAY,
    glTexBuffer,
    glTexBufferRange,
    glTexParameterIiv,
    glTexParameterIuiv,
    glGetTexParameterIiv,
    glGetTexParameterIuiv,
    glSamplerParameterIiv,
    glSamplerParameterIuiv,
    glGetSamplerParameterIiv,
    glGetSamplerParameterIuiv,
    glTexStorage3DMultisample,
    glReadnPixels,
    glGetnUniformfv,
    glGetnUniformiv,
    glGetnUniformuiv,
    glGetGraphicsResetStatus,
)

VERTEX = '''#version 320 es
in vec4 position;
void main() { gl_Position = position; }'''

FRAGMENT = '''#version 320 es
precision mediump float;
uniform vec4 color;
out vec4 fragColor;
void main() { fragColor = color; }'''


class TestES32TextureRobust(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def test_texture_buffer(self):
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'u4'), GL_STATIC_DRAW)
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_BUFFER, tex)
        glTexBuffer(GL_TEXTURE_BUFFER, GL_R32UI, buf)
        glTexBufferRange(GL_TEXTURE_BUFFER, GL_R32UI, buf, 0, 64)
        self.check_error('texture buffer')

    def test_integer_params(self):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameterIiv(
            GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'i')
        )
        glTexParameterIuiv(
            GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'u4')
        )
        ibuf = np.zeros(4, 'i')
        glGetTexParameterIiv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, ibuf)
        ubuf = np.zeros(4, 'u4')
        glGetTexParameterIuiv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, ubuf)

        sampler = one(glGenSamplers(1))
        glSamplerParameterIiv(
            sampler, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'i')
        )
        glSamplerParameterIuiv(
            sampler, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'u4')
        )
        glGetSamplerParameterIiv(sampler, GL_TEXTURE_BORDER_COLOR, ibuf)
        glGetSamplerParameterIuiv(sampler, GL_TEXTURE_BORDER_COLOR, ubuf)
        self.check_error('integer params')
        glDeleteSamplers(1, object_names(sampler))

    def test_multisample_array_storage(self):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, tex)
        glTexStorage3DMultisample(
            GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 8, 8, 2, True
        )
        self.check_error('multisample array storage')

    def test_robustness_queries(self):
        self.assertEqual(one(glGetGraphicsResetStatus()), int(GL_NO_ERROR))

        size = self.width * self.height * 4
        buf = (ctypes.c_ubyte * size)()
        glReadnPixels(
            0, 0, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, size, buf
        )

        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        loc = glGetUniformLocation(program, 'color')
        fbuf = np.zeros(4, 'f')
        glGetnUniformfv(program, loc, 16, fbuf)
        ibuf = np.zeros(4, 'i')
        glGetnUniformiv(program, loc, 16, ibuf)
        ubuf = np.zeros(4, 'u4')
        glGetnUniformuiv(program, loc, 16, ubuf)
        self.check_error('robustness queries')


if __name__ == '__main__':
    unittest.main()
