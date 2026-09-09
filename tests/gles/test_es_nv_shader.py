#! /usr/bin/env python3
"""NVIDIA OpenGL-ES shader / image / mesh extensions: bindless texture handles,
64-bit integer uniforms (gpu_shader5), the shading-rate image, mesh shading and
timeline semaphores.

Functional tests -- real objects and real calls with a clean error state.
Memory-object and Vulkan interop extensions are skipped with a reason.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import *  # noqa: F401,F403

I64 = '''#version 320 es
#extension GL_NV_gpu_shader5 : require
precision highp float; precision highp int;
uniform int64_t i1; uniform i64vec2 i2; uniform i64vec3 i3; uniform i64vec4 i4;
uniform uint64_t u1; uniform u64vec2 u2; uniform u64vec3 u3; uniform u64vec4 u4;
void main(){ gl_Position = vec4(float(i1 + i2.x + i3.y + i4.z)
  + float(u1 + u2.x + u3.y + u4.z)); }'''
MESH = '''#version 320 es
#extension GL_NV_mesh_shader : require
layout(local_size_x=1) in;
layout(triangles, max_vertices=3, max_primitives=1) out;
void main(){
    gl_PrimitiveCountNV = 1u;
    gl_MeshVerticesNV[0].gl_Position = vec4(-1.0, -1.0, 0.0, 1.0);
    gl_MeshVerticesNV[1].gl_Position = vec4( 3.0, -1.0, 0.0, 1.0);
    gl_MeshVerticesNV[2].gl_Position = vec4(-1.0,  3.0, 0.0, 1.0);
    gl_PrimitiveIndicesNV[0] = 0u; gl_PrimitiveIndicesNV[1] = 1u; gl_PrimitiveIndicesNV[2] = 2u;
}'''
MESH_FRAG = '#version 320 es\nprecision mediump float; out vec4 c; void main(){ c = vec4(1.0); }'


class TestESNVShader(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def test_nv_bindless_texture(self):
        self.require_extension('GL_NV_bindless_texture')
        from OpenGL.GLES2.NV.bindless_texture import (
            glGetTextureHandleNV, glGetTextureSamplerHandleNV,
            glMakeTextureHandleResidentNV, glMakeTextureHandleNonResidentNV,
            glIsTextureHandleResidentNV, glGetImageHandleNV,
            glMakeImageHandleResidentNV, glMakeImageHandleNonResidentNV,
            glIsImageHandleResidentNV, glUniformHandleui64NV,
            glUniformHandleui64vNV, glProgramUniformHandleui64NV,
            glProgramUniformHandleui64vNV,
        )
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        sampler = one(glGenSamplers(1))
        glSamplerParameteri(sampler, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        handle = one(glGetTextureHandleNV(tex))
        self.assertTrue(handle)
        self.assertTrue(one(glGetTextureSamplerHandleNV(tex, sampler)))
        glMakeTextureHandleResidentNV(handle)
        self.assertTrue(glIsTextureHandleResidentNV(handle))
        img = one(glGetImageHandleNV(tex, 0, GL_FALSE, 0, GL_RGBA8))
        glMakeImageHandleResidentNV(img, GL_READ_ONLY)
        self.assertTrue(glIsImageHandleResidentNV(img))
        glMakeImageHandleNonResidentNV(img)

        from OpenGL.GLES2 import shaders
        program = shaders.compileProgram(
            shaders.compileShader('#version 320 es\nvoid main(){ gl_Position = vec4(0.0); }', GL_VERTEX_SHADER),
            shaders.compileShader('#version 320 es\n#extension GL_NV_bindless_texture : require\n'
                                  'precision mediump float; uniform sampler2D s; out vec4 c;\n'
                                  'void main(){ c = texture(s, vec2(0.5)); }', GL_FRAGMENT_SHADER),
            validate=False)
        loc = glGetUniformLocation(program, 's')
        glUseProgram(program)
        glUniformHandleui64NV(loc, handle)
        glUniformHandleui64vNV(loc, 1, np.array([handle], 'u8'))
        glProgramUniformHandleui64NV(program, loc, handle)
        glProgramUniformHandleui64vNV(program, loc, 1, np.array([handle], 'u8'))
        glUseProgram(0)
        glMakeTextureHandleNonResidentNV(handle)
        self.check_error('es nv bindless texture')

    def test_nv_gpu_shader5(self):
        self.require_extension('GL_NV_gpu_shader5')
        from OpenGL.GLES2.NV.gpu_shader5 import (
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
        from OpenGL.GLES2 import shaders
        p = shaders.compileProgram(
            shaders.compileShader(I64, GL_VERTEX_SHADER),
            shaders.compileShader('#version 320 es\nprecision mediump float; out vec4 o; void main(){ o = vec4(1.0); }', GL_FRAGMENT_SHADER),
            validate=False)
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
        self.check_error('es nv gpu shader5')

    def test_nv_shading_rate_image(self):
        self.require_extension('GL_NV_shading_rate_image')
        from OpenGL.GLES2.NV.shading_rate_image import (
            glBindShadingRateImageNV, glShadingRateImageBarrierNV,
            glShadingRateImagePaletteNV, glGetShadingRateImagePaletteNV,
            glShadingRateSampleOrderNV, glGetShadingRateSampleLocationivNV,
            GL_SHADING_RATE_IMAGE_PALETTE_SIZE_NV,
            GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV,
            GL_SHADING_RATE_SAMPLE_ORDER_DEFAULT_NV,
        )
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_R8UI, 4, 4)
        glBindShadingRateImageNV(tex)
        glShadingRateImageBarrierNV(GL_TRUE)
        psize = int(self.getInteger(GL_SHADING_RATE_IMAGE_PALETTE_SIZE_NV)) or 1
        glShadingRateImagePaletteNV(0, 0, psize,
            np.array([GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV] * psize, 'u4'))
        glGetShadingRateImagePaletteNV(0, 0, np.zeros(1, 'u4'))
        glShadingRateSampleOrderNV(GL_SHADING_RATE_SAMPLE_ORDER_DEFAULT_NV)
        glGetShadingRateSampleLocationivNV(GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV, 0, 0, np.zeros(3, 'i'))
        glBindShadingRateImageNV(0)
        self.check_error('es nv shading rate image')

    def test_nv_mesh_shader(self):
        self.require_extension('GL_NV_mesh_shader')
        from OpenGL.GLES2.NV.mesh_shader import (
            glDrawMeshTasksNV, glDrawMeshTasksIndirectNV,
            glMultiDrawMeshTasksIndirectNV, glMultiDrawMeshTasksIndirectCountNV,
            GL_MESH_SHADER_NV,
        )
        from OpenGL.GLES2 import shaders
        program = shaders.compileProgram(
            shaders.compileShader(MESH, GL_MESH_SHADER_NV),
            shaders.compileShader(MESH_FRAG, GL_FRAGMENT_SHADER), validate=False)
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        glViewport(0, 0, 8, 8)
        glUseProgram(program)
        glDrawMeshTasksNV(0, 1)
        ind = one(glGenBuffers(1))
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, ind)
        glBufferData(GL_DRAW_INDIRECT_BUFFER, np.array([1, 0], 'u4'), GL_STATIC_DRAW)
        glDrawMeshTasksIndirectNV(0)
        glMultiDrawMeshTasksIndirectNV(0, 1, 0)
        param_buffer = 0x80EE  # GL_PARAMETER_BUFFER (indirect-parameters binding)
        pbuf = one(glGenBuffers(1))
        glBindBuffer(param_buffer, pbuf)
        glBufferData(param_buffer, np.array([0], 'u4'), GL_STATIC_DRAW)
        glMultiDrawMeshTasksIndirectCountNV(0, 0, 0, 0)
        glBindBuffer(param_buffer, 0)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, 0)
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('es nv mesh shader')

    def test_nv_timeline_semaphore(self):
        self.require_extension('GL_NV_timeline_semaphore')
        from OpenGL.GLES2.NV.timeline_semaphore import (
            glCreateSemaphoresNV, glSemaphoreParameterivNV, glGetSemaphoreParameterivNV,
            GL_SEMAPHORE_TYPE_NV, GL_SEMAPHORE_TYPE_TIMELINE_NV,
        )
        sems = np.zeros(1, 'u4')
        glCreateSemaphoresNV(1, sems)
        sem = int(sems[0])
        glSemaphoreParameterivNV(sem, GL_SEMAPHORE_TYPE_NV, np.array([GL_SEMAPHORE_TYPE_TIMELINE_NV], 'i'))
        glGetSemaphoreParameterivNV(sem, GL_SEMAPHORE_TYPE_NV, np.zeros(1, 'i'))
        self.check_error('es nv timeline semaphore')

    def test_nv_memory_attachment(self):
        self.require_extension('GL_NV_memory_attachment')
        self.skipTest('attaching memory objects requires externally-imported memory')

    def test_nv_memory_object_sparse(self):
        self.require_extension('GL_NV_memory_object_sparse')
        self.skipTest('memory-backed sparse commitment requires imported memory objects')

    def test_nv_draw_vulkan_image(self):
        self.require_extension('GL_NV_draw_vulkan_image')
        self.skipTest('Vulkan image/fence/semaphore interop is unavailable headless')


if __name__ == '__main__':
    unittest.main()
