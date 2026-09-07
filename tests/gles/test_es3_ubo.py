#! /usr/bin/env python3
"""GLES3.0: uniform blocks, unsigned/integer uniforms, non-square matrices,
integer vertex attributes and indexed/64-bit state queries."""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_UNIFORM_BUFFER,
    GL_STATIC_DRAW,
    GL_ARRAY_BUFFER,
    GL_INT,
    GL_UNIFORM_BLOCK_DATA_SIZE,
    GL_UNIFORM_TYPE,
    GL_MAX_ELEMENT_INDEX,
    GL_UNIFORM_BUFFER_BINDING,
    GL_CURRENT_VERTEX_ATTRIB,
    glUseProgram,
    glGetUniformLocation,
    glGetUniformBlockIndex,
    glGetActiveUniformBlockiv,
    glGetActiveUniformBlockName,
    glUniformBlockBinding,
    glGetActiveUniformsiv,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glBindBufferBase,
    glBindBufferRange,
    glUniform1ui,
    glUniform2ui,
    glUniform3ui,
    glUniform4ui,
    glUniform1uiv,
    glUniform2uiv,
    glUniform3uiv,
    glUniform4uiv,
    glGetUniformuiv,
    glUniformMatrix2x3fv,
    glUniformMatrix3x2fv,
    glUniformMatrix2x4fv,
    glUniformMatrix4x2fv,
    glUniformMatrix3x4fv,
    glUniformMatrix4x3fv,
    glVertexAttribI4i,
    glVertexAttribI4iv,
    glVertexAttribI4ui,
    glVertexAttribI4uiv,
    glVertexAttribIPointer,
    glGetVertexAttribIiv,
    glGetVertexAttribIuiv,
    glGetFragDataLocation,
    glGetIntegeri_v,
    glGetInteger64v,
    glGetInteger64i_v,
)

VERTEX = '''#version 300 es
in vec4 position;
in ivec4 iattr;
flat out int vi;
void main() { vi = iattr.x; gl_Position = position; }'''

FRAGMENT = '''#version 300 es
precision mediump float;
precision highp int;
uniform Block { vec4 blockColor; };
uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
flat in int vi;
out vec4 fragColor;
void main() {
    float m = m23[0][0] + m32[0][0] + m24[0][0] + m42[0][0] + m34[0][0] + m43[0][0];
    fragColor = blockColor
        + vec4(float(uu + uu2.x + uu3.y + uu4.z))
        + vec4(m) + vec4(float(vi));
}'''


class TestES3UBO(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_uniform_blocks(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)

        index = glGetUniformBlockIndex(program, 'Block')
        self.assertNotEqual(index, 0xFFFFFFFF)
        size = np.zeros(1, 'i')
        glGetActiveUniformBlockiv(program, index, GL_UNIFORM_BLOCK_DATA_SIZE, size)
        self.assertGreaterEqual(int(size[0]), 16)
        length, chars = glGetActiveUniformBlockName(program, index, 64)
        name = bytes(bytearray(int(c) for c in chars[: one(length)])).decode()
        self.assertIn('Block', name)
        glUniformBlockBinding(program, index, 0)

        params = np.zeros(1, 'i')
        glGetActiveUniformsiv(program, 1, np.array([0], 'u4'), GL_UNIFORM_TYPE, params)
        self.assertGreater(int(params[0]), 0)

        ubo = one(glGenBuffers(1))
        glBindBuffer(GL_UNIFORM_BUFFER, ubo)
        glBufferData(GL_UNIFORM_BUFFER, 16, np.ones(4, 'f'), GL_STATIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, 0, ubo)
        glBindBufferRange(GL_UNIFORM_BUFFER, 0, ubo, 0, 16)
        self.check_error('uniform block')

    def test_uint_uniforms(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        def loc(n):
            return glGetUniformLocation(program, n)
        glUniform1ui(loc('uu'), 1)
        glUniform2ui(loc('uu2'), 1, 2)
        glUniform3ui(loc('uu3'), 1, 2, 3)
        glUniform4ui(loc('uu4'), 1, 2, 3, 4)
        glUniform1uiv(loc('uu'), 1, np.array([5], 'u4'))
        glUniform2uiv(loc('uu2'), 1, np.array([5, 6], 'u4'))
        glUniform3uiv(loc('uu3'), 1, np.array([5, 6, 7], 'u4'))
        glUniform4uiv(loc('uu4'), 1, np.array([5, 6, 7, 8], 'u4'))
        buf = np.zeros(1, 'u4')
        glGetUniformuiv(program, loc('uu'), buf)
        self.assertEqual(int(buf[0]), 5)
        self.check_error('uint uniforms')

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

    def test_integer_attributes(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        self.assertNotEqual(glGetFragDataLocation(program, 'fragColor'), -1)
        glVertexAttribI4i(2, 1, 2, 3, 4)
        glVertexAttribI4iv(2, np.array([1, 2, 3, 4], 'i'))
        glVertexAttribI4ui(2, 1, 2, 3, 4)
        glVertexAttribI4uiv(2, np.array([1, 2, 3, 4], 'u4'))
        glGetVertexAttribIiv(2, GL_CURRENT_VERTEX_ATTRIB)
        glGetVertexAttribIuiv(2, GL_CURRENT_VERTEX_ATTRIB)
        # bind an integer attribute pointer from a buffer
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'i'), GL_STATIC_DRAW)
        glVertexAttribIPointer(2, 4, GL_INT, 0, None)
        self.check_error('integer attributes')

    def test_indexed_and_64bit_queries(self):
        big = np.zeros(1, 'q')
        glGetInteger64v(GL_MAX_ELEMENT_INDEX, big)
        self.assertGreater(int(big[0]), 0)
        out = np.zeros(1, 'i')
        glGetIntegeri_v(GL_UNIFORM_BUFFER_BINDING, 0, out)
        out64 = np.zeros(1, 'q')
        glGetInteger64i_v(GL_UNIFORM_BUFFER_BINDING, 0, out64)
        self.check_error('indexed/64-bit queries')


if __name__ == '__main__':
    unittest.main()
