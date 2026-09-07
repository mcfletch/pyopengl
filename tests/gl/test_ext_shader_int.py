#! /usr/bin/env python3
"""Integer/64-bit shader I/O extensions: GL_ARB_gpu_shader_int64,
GL_AMD_gpu_shader_int64 (its NV-named alias), GL_EXT_vertex_attrib_64bit,
GL_EXT_gpu_shader4 -- exercised against real programs in a core context."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.gpu_shader_int64 import *  # noqa: F401,F403
from OpenGL.GL.AMD.gpu_shader_int64 import *  # noqa: F401,F403
from OpenGL.GL.EXT.vertex_attrib_64bit import *  # noqa: F401,F403
from OpenGL.GL.EXT.gpu_shader4 import *  # noqa: F401,F403

VS = '#version 150\nin vec4 p; void main(){ gl_Position = p; }'

I64_FS = '''#version 450
#extension GL_ARB_gpu_shader_int64 : require
uniform int64_t i1; uniform i64vec2 i2; uniform i64vec3 i3; uniform i64vec4 i4;
uniform uint64_t u1; uniform u64vec2 u2; uniform u64vec3 u3; uniform u64vec4 u4;
out vec4 c;
void main(){ c = vec4(float(i1+i2.x+i3.y+i4.z) + float(u1+u2.x+u3.y+u4.z)); }'''

UINT_FS = '''#version 150
uniform uint u1; uniform uvec2 u2; uniform uvec3 u3; uniform uvec4 u4;
flat in uvec4 vi; out vec4 fc;
void main(){ fc = vec4(float(u1+u2.x+u3.y+u4.z+vi.x)); }'''
UINT_VS = '#version 150\nin vec4 p; in ivec4 ai; flat out uvec4 vi;\nvoid main(){ vi = uvec4(ai); gl_Position = p; }'


class TestGPUShaderInt64(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_int64_uniforms(self):
        self.require_extension('GL_ARB_gpu_shader_int64')
        with self.allow_missing():
            prog = self.compile_program(VS.replace('150', '450'), I64_FS)
            glUseProgram(prog)
            def L(n):
                return glGetUniformLocation(prog, n)
            glUniform1i64ARB(L('i1'), 1)
            glUniform1i64vARB(L('i1'), 1, np.array([1], 'q'))
            glUniform2i64ARB(L('i2'), 1, 2)
            glUniform2i64vARB(L('i2'), 1, np.array([1, 2], 'q'))
            glUniform3i64ARB(L('i3'), 1, 2, 3)
            glUniform3i64vARB(L('i3'), 1, np.array([1, 2, 3], 'q'))
            glUniform4i64ARB(L('i4'), 1, 2, 3, 4)
            glUniform4i64vARB(L('i4'), 1, np.array([1, 2, 3, 4], 'q'))
            glUniform1ui64ARB(L('u1'), 1)
            glUniform1ui64vARB(L('u1'), 1, np.array([1], 'Q'))
            glUniform2ui64ARB(L('u2'), 1, 2)
            glUniform2ui64vARB(L('u2'), 1, np.array([1, 2], 'Q'))
            glUniform3ui64ARB(L('u3'), 1, 2, 3)
            glUniform3ui64vARB(L('u3'), 1, np.array([1, 2, 3], 'Q'))
            glUniform4ui64ARB(L('u4'), 1, 2, 3, 4)
            glUniform4ui64vARB(L('u4'), 1, np.array([1, 2, 3, 4], 'Q'))
            glGetUniformi64vARB(prog, L('i1'), np.zeros(1, 'q'))
            glGetUniformui64vARB(prog, L('u1'), np.zeros(1, 'Q'))
            glGetnUniformi64vARB(prog, L('i1'), 8, np.zeros(1, 'q'))
            glGetnUniformui64vARB(prog, L('u1'), 8, np.zeros(1, 'Q'))
            glProgramUniform1i64ARB(prog, L('i1'), 1)
            glProgramUniform1i64vARB(prog, L('i1'), 1, np.array([1], 'q'))
            glProgramUniform2i64ARB(prog, L('i2'), 1, 2)
            glProgramUniform2i64vARB(prog, L('i2'), 1, np.array([1, 2], 'q'))
            glProgramUniform3i64ARB(prog, L('i3'), 1, 2, 3)
            glProgramUniform3i64vARB(prog, L('i3'), 1, np.array([1, 2, 3], 'q'))
            glProgramUniform4i64ARB(prog, L('i4'), 1, 2, 3, 4)
            glProgramUniform4i64vARB(prog, L('i4'), 1, np.array([1, 2, 3, 4], 'q'))
            glProgramUniform1ui64ARB(prog, L('u1'), 1)
            glProgramUniform1ui64vARB(prog, L('u1'), 1, np.array([1], 'Q'))
            glProgramUniform2ui64ARB(prog, L('u2'), 1, 2)
            glProgramUniform2ui64vARB(prog, L('u2'), 1, np.array([1, 2], 'Q'))
            glProgramUniform3ui64ARB(prog, L('u3'), 1, 2, 3)
            glProgramUniform3ui64vARB(prog, L('u3'), 1, np.array([1, 2, 3], 'Q'))
            glProgramUniform4ui64ARB(prog, L('u4'), 1, 2, 3, 4)
            glProgramUniform4ui64vARB(prog, L('u4'), 1, np.array([1, 2, 3, 4], 'Q'))
        self.check_error('int64 uniforms')

    def test_int64_uniforms_amd(self):
        """GL_AMD_gpu_shader_int64: the NV-suffixed alias of the ARB int64
        uniform family (same int64 GLSL, glUniform*64NV / glProgramUniform*64NV
        entry points)."""
        self.require_extension('GL_AMD_gpu_shader_int64')
        with self.allow_missing():
            prog = self.compile_program(VS.replace('150', '450'), I64_FS)
            glUseProgram(prog)

            def L(n):
                return glGetUniformLocation(prog, n)

            glUniform1i64NV(L('i1'), 1)
            glUniform1i64vNV(L('i1'), 1, np.array([1], 'q'))
            glUniform2i64NV(L('i2'), 1, 2)
            glUniform2i64vNV(L('i2'), 1, np.array([1, 2], 'q'))
            glUniform3i64NV(L('i3'), 1, 2, 3)
            glUniform3i64vNV(L('i3'), 1, np.array([1, 2, 3], 'q'))
            glUniform4i64NV(L('i4'), 1, 2, 3, 4)
            glUniform4i64vNV(L('i4'), 1, np.array([1, 2, 3, 4], 'q'))
            glUniform1ui64NV(L('u1'), 1)
            glUniform1ui64vNV(L('u1'), 1, np.array([1], 'Q'))
            glUniform2ui64NV(L('u2'), 1, 2)
            glUniform2ui64vNV(L('u2'), 1, np.array([1, 2], 'Q'))
            glUniform3ui64NV(L('u3'), 1, 2, 3)
            glUniform3ui64vNV(L('u3'), 1, np.array([1, 2, 3], 'Q'))
            glUniform4ui64NV(L('u4'), 1, 2, 3, 4)
            glUniform4ui64vNV(L('u4'), 1, np.array([1, 2, 3, 4], 'Q'))
            glGetUniformi64vNV(prog, L('i1'), np.zeros(1, 'q'))
            glGetUniformui64vNV(prog, L('u1'), np.zeros(1, 'Q'))
            glProgramUniform1i64NV(prog, L('i1'), 1)
            glProgramUniform1i64vNV(prog, L('i1'), 1, np.array([1], 'q'))
            glProgramUniform2i64NV(prog, L('i2'), 1, 2)
            glProgramUniform2i64vNV(prog, L('i2'), 1, np.array([1, 2], 'q'))
            glProgramUniform3i64NV(prog, L('i3'), 1, 2, 3)
            glProgramUniform3i64vNV(prog, L('i3'), 1, np.array([1, 2, 3], 'q'))
            glProgramUniform4i64NV(prog, L('i4'), 1, 2, 3, 4)
            glProgramUniform4i64vNV(prog, L('i4'), 1, np.array([1, 2, 3, 4], 'q'))
            glProgramUniform1ui64NV(prog, L('u1'), 1)
            glProgramUniform1ui64vNV(prog, L('u1'), 1, np.array([1], 'Q'))
            glProgramUniform2ui64NV(prog, L('u2'), 1, 2)
            glProgramUniform2ui64vNV(prog, L('u2'), 1, np.array([1, 2], 'Q'))
            glProgramUniform3ui64NV(prog, L('u3'), 1, 2, 3)
            glProgramUniform3ui64vNV(prog, L('u3'), 1, np.array([1, 2, 3], 'Q'))
            glProgramUniform4ui64NV(prog, L('u4'), 1, 2, 3, 4)
            glProgramUniform4ui64vNV(prog, L('u4'), 1, np.array([1, 2, 3, 4], 'Q'))
        self.check_error('AMD int64 uniforms')

    def test_attrib_64bit(self):
        self.require_extension('GL_EXT_vertex_attrib_64bit')
        with self.allow_missing():
            glVertexAttribL1dEXT(1, 1.0)
            glVertexAttribL1dvEXT(1, np.zeros(1, 'd'))
            glVertexAttribL2dEXT(1, 1, 2)
            glVertexAttribL2dvEXT(1, np.zeros(2, 'd'))
            glVertexAttribL3dEXT(1, 1, 2, 3)
            glVertexAttribL3dvEXT(1, np.zeros(3, 'd'))
            glVertexAttribL4dEXT(1, 1, 2, 3, 4)
            glVertexAttribL4dvEXT(1, np.zeros(4, 'd'))
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, np.zeros(8, 'd'), GL_STATIC_DRAW)
            glVertexAttribLPointerEXT(1, 4, GL_DOUBLE, 0, None)
            glGetVertexAttribLdvEXT(1, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'd'))
        self.check_error('attrib 64-bit')


class TestGPUShader4(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_gpu_shader4(self):
        self.require_extension('GL_EXT_gpu_shader4')
        with self.allow_missing():
            from OpenGL.GL import shaders

            vs = shaders.compileShader(UINT_VS, GL_VERTEX_SHADER)
            fs = shaders.compileShader(UINT_FS, GL_FRAGMENT_SHADER)
            prog = glCreateProgram()
            glAttachShader(prog, vs)
            glAttachShader(prog, fs)
            glBindFragDataLocationEXT(prog, 0, b'fc')
            glLinkProgram(prog)
            glUseProgram(prog)
            self.assertEqual(glGetFragDataLocationEXT(prog, b'fc'), 0)
            def L(n):
                return glGetUniformLocation(prog, n)
            glUniform1uiEXT(L('u1'), 1)
            glUniform1uivEXT(L('u1'), 1, np.array([1], 'I'))
            glUniform2uiEXT(L('u2'), 1, 2)
            glUniform2uivEXT(L('u2'), 1, np.array([1, 2], 'I'))
            glUniform3uiEXT(L('u3'), 1, 2, 3)
            glUniform3uivEXT(L('u3'), 1, np.array([1, 2, 3], 'I'))
            glUniform4uiEXT(L('u4'), 1, 2, 3, 4)
            glUniform4uivEXT(L('u4'), 1, np.array([1, 2, 3, 4], 'I'))
            glGetUniformuivEXT(prog, L('u1'), np.zeros(1, 'I'))
            ai = glGetAttribLocation(prog, 'ai')
            glVertexAttribI1iEXT(ai, 1)
            glVertexAttribI1ivEXT(ai, np.array([1], 'i'))
            glVertexAttribI1uiEXT(ai, 1)
            glVertexAttribI1uivEXT(ai, np.array([1], 'I'))
            glVertexAttribI2iEXT(ai, 1, 2)
            glVertexAttribI2ivEXT(ai, np.array([1, 2], 'i'))
            glVertexAttribI2uiEXT(ai, 1, 2)
            glVertexAttribI2uivEXT(ai, np.array([1, 2], 'I'))
            glVertexAttribI3iEXT(ai, 1, 2, 3)
            glVertexAttribI3ivEXT(ai, np.array([1, 2, 3], 'i'))
            glVertexAttribI3uiEXT(ai, 1, 2, 3)
            glVertexAttribI3uivEXT(ai, np.array([1, 2, 3], 'I'))
            glVertexAttribI4iEXT(ai, 1, 2, 3, 4)
            glVertexAttribI4ivEXT(ai, np.array([1, 2, 3, 4], 'i'))
            glVertexAttribI4uiEXT(ai, 1, 2, 3, 4)
            glVertexAttribI4uivEXT(ai, np.array([1, 2, 3, 4], 'I'))
            glVertexAttribI4bvEXT(ai, np.zeros(4, 'b'))
            glVertexAttribI4svEXT(ai, np.zeros(4, 'h'))
            glVertexAttribI4ubvEXT(ai, np.zeros(4, 'B'))
            glVertexAttribI4usvEXT(ai, np.zeros(4, 'H'))
            glGetVertexAttribIivEXT(
                ai, GL_VERTEX_ATTRIB_ARRAY_ENABLED, np.zeros(1, 'i')
            )
            glGetVertexAttribIuivEXT(
                ai, GL_VERTEX_ATTRIB_ARRAY_ENABLED, np.zeros(1, 'I')
            )
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'i'), GL_STATIC_DRAW)
            glVertexAttribIPointerEXT(ai, 4, GL_INT, 0, None)
        self.check_error('gpu shader4')


if __name__ == '__main__':
    unittest.main()
