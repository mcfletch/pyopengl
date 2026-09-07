#! /usr/bin/env python3
"""NVIDIA desktop-GL shader / buffer-address extensions: 64-bit integer uniforms
(NV_gpu_shader5), resident buffer GPU addresses (NV_shader_buffer_load), 64-bit
integer vertex attributes (NV_vertex_attrib_integer_64bit), unified-memory vertex
formats (NV_vertex_buffer_unified_memory) and bindless multi-draw-indirect.

Functional tests -- real objects, real calls, clean error state.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403

I64UNIFORMS = '''#version 450 core
#extension GL_NV_gpu_shader5 : require
uniform int64_t i1; uniform i64vec2 i2; uniform i64vec3 i3; uniform i64vec4 i4;
uniform uint64_t u1; uniform u64vec2 u2; uniform u64vec3 u3; uniform u64vec4 u4;
out vec4 c;
void main(){
    c = vec4(float(i1 + i2.x + i3.y + i4.z) + float(u1 + u2.x + u3.y + u4.z));
}'''


class TestNVShader(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def _i64_program(self):
        return self.compile_program(
            '#version 450 core\nvoid main(){gl_Position=vec4(0.0);}', I64UNIFORMS
        )

    # --- GL_NV_gpu_shader5 -----------------------------------------------
    def test_nv_gpu_shader5(self):
        self.require_extension('GL_NV_gpu_shader5')
        from OpenGL.GL.NV.gpu_shader5 import (
            glUniform1i64NV, glUniform2i64NV, glUniform3i64NV, glUniform4i64NV,
            glUniform1ui64NV, glUniform2ui64NV, glUniform3ui64NV, glUniform4ui64NV,
            glUniform1i64vNV, glUniform2i64vNV, glUniform3i64vNV, glUniform4i64vNV,
            glUniform1ui64vNV, glUniform2ui64vNV, glUniform3ui64vNV, glUniform4ui64vNV,
            glProgramUniform1i64NV, glProgramUniform2i64NV, glProgramUniform3i64NV,
            glProgramUniform4i64NV, glProgramUniform1ui64NV, glProgramUniform2ui64NV,
            glProgramUniform3ui64NV, glProgramUniform4ui64NV,
            glProgramUniform1i64vNV, glProgramUniform2i64vNV, glProgramUniform3i64vNV,
            glProgramUniform4i64vNV, glProgramUniform1ui64vNV, glProgramUniform2ui64vNV,
            glProgramUniform3ui64vNV, glProgramUniform4ui64vNV, glGetUniformi64vNV,
        )

        p = self._i64_program()
        glUseProgram(p)

        def L(n):
            return glGetUniformLocation(p, n)

        glUniform1i64NV(L('i1'), 1)
        glUniform2i64NV(L('i2'), 1, 2)
        glUniform3i64NV(L('i3'), 1, 2, 3)
        glUniform4i64NV(L('i4'), 1, 2, 3, 4)
        glUniform1ui64NV(L('u1'), 1)
        glUniform2ui64NV(L('u2'), 1, 2)
        glUniform3ui64NV(L('u3'), 1, 2, 3)
        glUniform4ui64NV(L('u4'), 1, 2, 3, 4)
        glUniform1i64vNV(L('i1'), 1, np.array([1], 'i8'))
        glUniform2i64vNV(L('i2'), 1, np.array([1, 2], 'i8'))
        glUniform3i64vNV(L('i3'), 1, np.array([1, 2, 3], 'i8'))
        glUniform4i64vNV(L('i4'), 1, np.array([1, 2, 3, 4], 'i8'))
        glUniform1ui64vNV(L('u1'), 1, np.array([1], 'u8'))
        glUniform2ui64vNV(L('u2'), 1, np.array([1, 2], 'u8'))
        glUniform3ui64vNV(L('u3'), 1, np.array([1, 2, 3], 'u8'))
        glUniform4ui64vNV(L('u4'), 1, np.array([1, 2, 3, 4], 'u8'))

        glProgramUniform1i64NV(p, L('i1'), 1)
        glProgramUniform2i64NV(p, L('i2'), 1, 2)
        glProgramUniform3i64NV(p, L('i3'), 1, 2, 3)
        glProgramUniform4i64NV(p, L('i4'), 1, 2, 3, 4)
        glProgramUniform1ui64NV(p, L('u1'), 1)
        glProgramUniform2ui64NV(p, L('u2'), 1, 2)
        glProgramUniform3ui64NV(p, L('u3'), 1, 2, 3)
        glProgramUniform4ui64NV(p, L('u4'), 1, 2, 3, 4)
        glProgramUniform1i64vNV(p, L('i1'), 1, np.array([1], 'i8'))
        glProgramUniform2i64vNV(p, L('i2'), 1, np.array([1, 2], 'i8'))
        glProgramUniform3i64vNV(p, L('i3'), 1, np.array([1, 2, 3], 'i8'))
        glProgramUniform4i64vNV(p, L('i4'), 1, np.array([1, 2, 3, 4], 'i8'))
        glProgramUniform1ui64vNV(p, L('u1'), 1, np.array([1], 'u8'))
        glProgramUniform2ui64vNV(p, L('u2'), 1, np.array([1, 2], 'u8'))
        glProgramUniform3ui64vNV(p, L('u3'), 1, np.array([1, 2, 3], 'u8'))
        glProgramUniform4ui64vNV(p, L('u4'), 1, np.array([1, 2, 3, 4], 'u8'))
        glGetUniformi64vNV(p, L('i1'), np.zeros(1, 'i8'))
        glUseProgram(0)
        self.check_error('nv gpu shader5')

    # --- GL_NV_shader_buffer_load ----------------------------------------
    def test_nv_shader_buffer_load(self):
        self.require_extension('GL_NV_shader_buffer_load')
        from OpenGL.GL.NV.shader_buffer_load import (
            glMakeBufferResidentNV, glMakeBufferNonResidentNV, glIsBufferResidentNV,
            glMakeNamedBufferResidentNV, glMakeNamedBufferNonResidentNV,
            glIsNamedBufferResidentNV, glGetBufferParameterui64vNV,
            glGetNamedBufferParameterui64vNV, glGetIntegerui64vNV,
            glUniformui64NV, glUniformui64vNV, glProgramUniformui64NV,
            glProgramUniformui64vNV, GL_BUFFER_GPU_ADDRESS_NV,
            GL_MAX_SHADER_BUFFER_ADDRESS_NV,
        )

        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, 256, None, GL_STATIC_DRAW)
        glMakeBufferResidentNV(GL_ARRAY_BUFFER, GL_READ_ONLY)
        self.assertTrue(glIsBufferResidentNV(GL_ARRAY_BUFFER))
        addr = np.zeros(1, 'u8')
        glGetBufferParameterui64vNV(GL_ARRAY_BUFFER, GL_BUFFER_GPU_ADDRESS_NV, addr)
        glMakeBufferNonResidentNV(GL_ARRAY_BUFFER)

        glMakeNamedBufferResidentNV(buf, GL_READ_ONLY)
        self.assertTrue(glIsNamedBufferResidentNV(buf))
        glGetNamedBufferParameterui64vNV(buf, GL_BUFFER_GPU_ADDRESS_NV, np.zeros(1, 'u8'))
        glMakeNamedBufferNonResidentNV(buf)
        glGetIntegerui64vNV(GL_MAX_SHADER_BUFFER_ADDRESS_NV, np.zeros(1, 'u8'))

        # uint64 ("buffer address") uniform setters
        p = self.compile_program(
            '#version 450 core\nvoid main(){gl_Position=vec4(0.0);}',
            '#version 450 core\n'
            '#extension GL_NV_gpu_shader5 : require\n'
            'uniform uint64_t ptr; out vec4 c;\n'
            'void main(){ c = vec4(float(ptr)); }',
        )
        loc = glGetUniformLocation(p, 'ptr')
        gpu_addr = int(addr[0])
        glUseProgram(p)
        glUniformui64NV(loc, gpu_addr)
        glUniformui64vNV(loc, 1, np.array([gpu_addr], 'u8'))
        glProgramUniformui64NV(p, loc, gpu_addr)
        glProgramUniformui64vNV(p, loc, 1, np.array([gpu_addr], 'u8'))
        from OpenGL.GL.NV.shader_buffer_load import glGetUniformui64vNV
        glGetUniformui64vNV(p, loc, np.zeros(1, 'u8'))
        glUseProgram(0)
        self.check_error('nv shader buffer load')

    # --- GL_NV_vertex_attrib_integer_64bit -------------------------------
    def test_nv_vertex_attrib_integer_64bit(self):
        self.require_extension('GL_NV_vertex_attrib_integer_64bit')
        from OpenGL.GL.NV.vertex_attrib_integer_64bit import (
            glVertexAttribL1i64NV, glVertexAttribL2i64NV, glVertexAttribL3i64NV,
            glVertexAttribL4i64NV, glVertexAttribL1ui64NV, glVertexAttribL2ui64NV,
            glVertexAttribL3ui64NV, glVertexAttribL4ui64NV, glVertexAttribL1i64vNV,
            glVertexAttribL2i64vNV, glVertexAttribL3i64vNV, glVertexAttribL4i64vNV,
            glVertexAttribL1ui64vNV, glVertexAttribL2ui64vNV, glVertexAttribL3ui64vNV,
            glVertexAttribL4ui64vNV, glVertexAttribLFormatNV,
            glGetVertexAttribLi64vNV, glGetVertexAttribLui64vNV, GL_INT64_NV,
        )

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        glVertexAttribL1i64NV(1, 1)
        glVertexAttribL2i64NV(1, 1, 2)
        glVertexAttribL3i64NV(1, 1, 2, 3)
        glVertexAttribL4i64NV(1, 1, 2, 3, 4)
        glVertexAttribL1ui64NV(2, 1)
        glVertexAttribL2ui64NV(2, 1, 2)
        glVertexAttribL3ui64NV(2, 1, 2, 3)
        glVertexAttribL4ui64NV(2, 1, 2, 3, 4)
        glVertexAttribL1i64vNV(1, np.array([1], 'i8'))
        glVertexAttribL2i64vNV(1, np.array([1, 2], 'i8'))
        glVertexAttribL3i64vNV(1, np.array([1, 2, 3], 'i8'))
        glVertexAttribL4i64vNV(1, np.array([1, 2, 3, 4], 'i8'))
        glVertexAttribL1ui64vNV(2, np.array([1], 'u8'))
        glVertexAttribL2ui64vNV(2, np.array([1, 2], 'u8'))
        glVertexAttribL3ui64vNV(2, np.array([1, 2, 3], 'u8'))
        glVertexAttribL4ui64vNV(2, np.array([1, 2, 3, 4], 'u8'))
        glVertexAttribLFormatNV(0, 4, GL_INT64_NV, 0)
        # GL_CURRENT_VERTEX_ATTRIB returns a 4-component value
        glGetVertexAttribLi64vNV(1, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'i8'))
        glGetVertexAttribLui64vNV(2, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'u8'))
        glBindVertexArray(0)
        self.check_error('nv vertex attrib integer 64bit')

    # --- GL_NV_vertex_buffer_unified_memory ------------------------------
    def test_nv_vertex_buffer_unified_memory(self):
        self.require_extension('GL_NV_vertex_buffer_unified_memory')
        self.require_extension('GL_NV_shader_buffer_load')
        from OpenGL.GL.NV.shader_buffer_load import (
            glMakeBufferResidentNV, glMakeBufferNonResidentNV,
            glGetBufferParameterui64vNV, GL_BUFFER_GPU_ADDRESS_NV,
        )
        from OpenGL.GL.NV.vertex_buffer_unified_memory import (
            glBufferAddressRangeNV, glVertexFormatNV, glNormalFormatNV,
            glColorFormatNV, glIndexFormatNV, glTexCoordFormatNV, glEdgeFlagFormatNV,
            glSecondaryColorFormatNV, glFogCoordFormatNV, glVertexAttribFormatNV,
            glVertexAttribIFormatNV, glGetIntegerui64i_vNV,
            GL_VERTEX_ATTRIB_ARRAY_UNIFIED_NV, GL_VERTEX_ATTRIB_ARRAY_ADDRESS_NV,
        )

        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, 256, None, GL_STATIC_DRAW)
        glMakeBufferResidentNV(GL_ARRAY_BUFFER, GL_READ_ONLY)
        addr = np.zeros(1, 'u8')
        glGetBufferParameterui64vNV(GL_ARRAY_BUFFER, GL_BUFFER_GPU_ADDRESS_NV, addr)

        glEnableClientState(GL_VERTEX_ATTRIB_ARRAY_UNIFIED_NV)
        glVertexAttribFormatNV(0, 4, GL_FLOAT, GL_FALSE, 16)
        glVertexAttribIFormatNV(1, 4, GL_INT, 16)
        glBufferAddressRangeNV(GL_VERTEX_ATTRIB_ARRAY_ADDRESS_NV, 0, int(addr[0]), 256)
        glVertexFormatNV(3, GL_FLOAT, 12)
        glNormalFormatNV(GL_FLOAT, 12)
        glColorFormatNV(4, GL_FLOAT, 16)
        glIndexFormatNV(GL_INT, 4)
        glTexCoordFormatNV(2, GL_FLOAT, 8)
        glEdgeFlagFormatNV(4)
        glSecondaryColorFormatNV(3, GL_FLOAT, 12)
        glFogCoordFormatNV(GL_FLOAT, 4)
        glGetIntegerui64i_vNV(GL_VERTEX_ATTRIB_ARRAY_ADDRESS_NV, 0, np.zeros(1, 'u8'))
        glDisableClientState(GL_VERTEX_ATTRIB_ARRAY_UNIFIED_NV)
        glMakeBufferNonResidentNV(GL_ARRAY_BUFFER)
        self.check_error('nv vertex buffer unified memory')

    # --- GL_NV_bindless_multi_draw_indirect (+ _count) -------------------
    def test_nv_bindless_multi_draw_indirect(self):
        self.require_extension('GL_NV_bindless_multi_draw_indirect')
        from OpenGL.GL.NV.bindless_multi_draw_indirect import (
            glMultiDrawArraysIndirectBindlessNV, glMultiDrawElementsIndirectBindlessNV,
        )

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        # a zero-draw multi-draw is a well-defined no-op that still drives the
        # entry point through the driver
        glMultiDrawArraysIndirectBindlessNV(GL_TRIANGLES, None, 0, 0, 0)
        glMultiDrawElementsIndirectBindlessNV(
            GL_TRIANGLES, GL_UNSIGNED_INT, None, 0, 0, 0
        )
        glBindVertexArray(0)
        self.check_error('nv bindless multi draw indirect')

    def test_nv_bindless_multi_draw_indirect_count(self):
        self.require_extension('GL_NV_bindless_multi_draw_indirect_count')
        from OpenGL.GL.NV.bindless_multi_draw_indirect_count import (
            glMultiDrawArraysIndirectBindlessCountNV,
            glMultiDrawElementsIndirectBindlessCountNV,
        )

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        # the *Count* variants read the draw count from a bound parameter buffer
        pbuf = one(glGenBuffers(1))
        glBindBuffer(GL_PARAMETER_BUFFER, pbuf)
        glBufferData(GL_PARAMETER_BUFFER, 4, np.zeros(1, 'u4'), GL_STATIC_DRAW)
        glMultiDrawArraysIndirectBindlessCountNV(GL_TRIANGLES, None, 0, 0, 0, 0)
        glMultiDrawElementsIndirectBindlessCountNV(
            GL_TRIANGLES, GL_UNSIGNED_INT, None, 0, 0, 0, 0
        )
        glBindBuffer(GL_PARAMETER_BUFFER, 0)
        glBindVertexArray(0)
        self.check_error('nv bindless multi draw indirect count')


if __name__ == '__main__':
    unittest.main()
