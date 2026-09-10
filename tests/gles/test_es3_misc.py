#! /usr/bin/env python3
"""GLES3.0: compressed 3D textures, copy-to-3D, VAO management, program binary."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_TEXTURE_2D_ARRAY,
    GL_RGBA8,
    GL_COMPRESSED_RGB8_ETC2,
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_PROGRAM_BINARY_RETRIEVABLE_HINT,
    GL_PROGRAM_BINARY_LENGTH,
    GL_ACTIVE_UNIFORMS,
    glGenTextures,
    glBindTexture,
    glTexStorage3D,
    glCompressedTexImage3D,
    glCompressedTexSubImage3D,
    glCopyTexSubImage3D,
    glGenVertexArrays,
    glBindVertexArray,
    glIsVertexArray,
    glDeleteVertexArrays,
    glCreateShader,
    glShaderSource,
    glCompileShader,
    glCreateProgram,
    glAttachShader,
    glLinkProgram,
    glGetProgramiv,
    glProgramParameteri,
    glGetProgramBinary,
    glProgramBinary,
    glGetUniformIndices,
    glGetActiveUniformsiv,
    GL_UNIFORM_TYPE,
)

VERTEX = '''#version 300 es
in vec4 position;
void main() { gl_Position = position; }'''

FRAGMENT = '''#version 300 es
precision mediump float;
uniform float uf;
out vec4 fragColor;
void main() { fragColor = vec4( uf ); }'''

ETC2_BLOCK = np.zeros(8, np.uint8)


class TestES3Misc(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_compressed_3d_and_copy(self):
        arr = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_ARRAY, arr)
        glCompressedTexImage3D(
            GL_TEXTURE_2D_ARRAY, 0, GL_COMPRESSED_RGB8_ETC2, 4, 4, 1, 0, 8, ETC2_BLOCK
        )
        glCompressedTexSubImage3D(
            GL_TEXTURE_2D_ARRAY,
            0,
            0,
            0,
            0,
            4,
            4,
            1,
            GL_COMPRESSED_RGB8_ETC2,
            8,
            ETC2_BLOCK,
        )
        # copy the (cleared) framebuffer into an uncompressed array layer
        copy = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_ARRAY, copy)
        glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 16, 16, 2)
        glCopyTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, 0, 0, 0, 16, 16)
        self.check_error('compressed 3d / copy')

    def test_vertex_array_objects(self):
        vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(vao))
        self.assertTrue(glIsVertexArray(vao))
        glBindVertexArray(0)
        glDeleteVertexArrays(1, object_names(vao))
        self.assertFalse(glIsVertexArray(vao))

    def test_uniform_indices(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        n = one(glGetProgramiv(program, GL_ACTIVE_UNIFORMS))
        self.assertGreaterEqual(one(n), 1)
        indices = glGetUniformIndices(program, ['uf'])
        self.assertNotEqual(int(indices[0]), 0xFFFFFFFF)
        types = np.zeros(1, 'i')
        glGetActiveUniformsiv(program, 1, indices, GL_UNIFORM_TYPE, types)
        self.check_error('uniform indices')

    def test_program_binary(self):
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, VERTEX)
        glCompileShader(vs)
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, FRAGMENT)
        glCompileShader(fs)
        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glProgramParameteri(program, GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE)
        glLinkProgram(program)
        self.assertEqual(one(glGetProgramiv(program, GL_LINK_STATUS)), GL_TRUE)

        length = one(glGetProgramiv(program, GL_PROGRAM_BINARY_LENGTH))
        if length < 1:
            self.skipTest('driver reports no retrievable program binary')
        out_len = (ctypes.c_int * 1)()
        out_fmt = (ctypes.c_uint * 1)()
        binary = (ctypes.c_ubyte * length)()
        glGetProgramBinary(program, length, out_len, out_fmt, binary)

        program2 = glCreateProgram()
        glProgramBinary(program2, out_fmt[0], binary, out_len[0])
        self.check_error('program binary')


if __name__ == '__main__':
    unittest.main()
