#! /usr/bin/env python3
"""NVIDIA OpenGL-ES state / rasterization / draw extensions beyond the Mesa
baseline: advanced blend, conservative raster, clip-space W scaling, buffer
copy, instanced draws/arrays, coverage-to-colour, framebuffer blit, mixed
samples, multisample renderbuffers, internalformat sample query, polygon mode,
sample locations, exclusive scissor, viewport swizzle, non-square matrix
uniforms and the viewport array.

Functional tests -- real objects and real calls with a clean error state.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import *  # noqa: F401,F403


class TestESNVState(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def _color_fbo(self, w=8, h=8):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, w, h)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        return fbo

    def _program(self):
        from OpenGL.GLES2 import shaders
        return shaders.compileProgram(
            shaders.compileShader(
                '#version 320 es\nin vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }',
                GL_VERTEX_SHADER),
            shaders.compileShader(
                '#version 320 es\nprecision mediump float; out vec4 c; void main(){ c = vec4(1.0); }',
                GL_FRAGMENT_SHADER),
        )

    def test_nv_blend_equation_advanced(self):
        self.require_extension('GL_NV_blend_equation_advanced')
        from OpenGL.GLES2.NV.blend_equation_advanced import (
            glBlendBarrierNV, glBlendParameteriNV, GL_BLEND_OVERLAP_NV, GL_CONJOINT_NV,
        )
        glBlendParameteriNV(GL_BLEND_OVERLAP_NV, GL_CONJOINT_NV)
        glBlendBarrierNV()
        self.check_error('es nv blend equation advanced')

    def test_nv_conservative_raster(self):
        self.require_extension('GL_NV_conservative_raster')
        from OpenGL.GLES2.NV.conservative_raster import glSubpixelPrecisionBiasNV
        glSubpixelPrecisionBiasNV(4, 4)
        glSubpixelPrecisionBiasNV(0, 0)
        self.check_error('es nv conservative raster')

    def test_nv_conservative_raster_pre_snap_triangles(self):
        self.require_extension('GL_NV_conservative_raster_pre_snap_triangles')
        from OpenGL.GLES2.NV.conservative_raster_pre_snap_triangles import (
            glConservativeRasterParameteriNV, GL_CONSERVATIVE_RASTER_MODE_NV,
            GL_CONSERVATIVE_RASTER_MODE_POST_SNAP_NV,
        )
        glConservativeRasterParameteriNV(
            GL_CONSERVATIVE_RASTER_MODE_NV, GL_CONSERVATIVE_RASTER_MODE_POST_SNAP_NV)
        self.check_error('es nv conservative raster pre snap')

    def test_nv_clip_space_w_scaling(self):
        self.require_extension('GL_NV_clip_space_w_scaling')
        from OpenGL.GLES2.NV.clip_space_w_scaling import glViewportPositionWScaleNV
        glViewportPositionWScaleNV(0, 1.0, 1.0)
        self.check_error('es nv clip space w scaling')

    def test_nv_copy_buffer(self):
        self.require_extension('GL_NV_copy_buffer')
        from OpenGL.GLES2.NV.copy_buffer import glCopyBufferSubDataNV
        a = one(glGenBuffers(1)); glBindBuffer(GL_ARRAY_BUFFER, a)
        glBufferData(GL_ARRAY_BUFFER, 64, None, GL_STATIC_DRAW)
        b = one(glGenBuffers(1)); glBindBuffer(GL_COPY_WRITE_BUFFER, b)
        glBufferData(GL_COPY_WRITE_BUFFER, 64, None, GL_STATIC_DRAW)
        glCopyBufferSubDataNV(GL_ARRAY_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0, 64)
        self.check_error('es nv copy buffer')

    def test_nv_draw_instanced(self):
        self.require_extension('GL_NV_draw_instanced')
        from OpenGL.GLES2.NV.draw_instanced import (
            glDrawArraysInstancedNV, glDrawElementsInstancedNV,
        )
        glUseProgram(self._program())
        vao = one(glGenVertexArrays(1)); glBindVertexArray(vao)
        glDrawArraysInstancedNV(GL_TRIANGLES, 0, 3, 2)
        idx = one(glGenBuffers(1)); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, idx)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'u4'), GL_STATIC_DRAW)
        glDrawElementsInstancedNV(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2)
        glUseProgram(0)
        self.check_error('es nv draw instanced')

    def test_nv_fragment_coverage_to_color(self):
        self.require_extension('GL_NV_fragment_coverage_to_color')
        from OpenGL.GLES2.NV.fragment_coverage_to_color import glFragmentCoverageColorNV
        tex = one(glGenTextures(1)); glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_R32UI, 8, 8)
        fbo = one(glGenFramebuffers(1)); glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        glFragmentCoverageColorNV(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('es nv fragment coverage to color')

    def test_nv_framebuffer_blit(self):
        self.require_extension('GL_NV_framebuffer_blit')
        from OpenGL.GLES2.NV.framebuffer_blit import glBlitFramebufferNV
        src = self._color_fbo()
        dst = self._color_fbo()
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst)
        glBlitFramebufferNV(0, 0, 8, 8, 0, 0, 8, 8, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('es nv framebuffer blit')

    def test_nv_framebuffer_mixed_samples(self):
        self.require_extension('GL_NV_framebuffer_mixed_samples')
        from OpenGL.GLES2.NV.framebuffer_mixed_samples import (
            glCoverageModulationNV, glCoverageModulationTableNV,
            glGetCoverageModulationTableNV, glRasterSamplesEXT,
            GL_COVERAGE_MODULATION_TABLE_SIZE_NV,
        )
        glRasterSamplesEXT(4, GL_TRUE)
        glCoverageModulationNV(GL_RGBA)
        size = int(self.getInteger(GL_COVERAGE_MODULATION_TABLE_SIZE_NV))
        if size > 0:
            glCoverageModulationTableNV(size, np.ones(size, 'f'))
            glGetCoverageModulationTableNV(size, np.zeros(size, 'f'))
        glRasterSamplesEXT(0, GL_FALSE)
        glCoverageModulationNV(GL_NONE)
        self.check_error('es nv framebuffer mixed samples')

    def test_nv_framebuffer_multisample(self):
        self.require_extension('GL_NV_framebuffer_multisample')
        from OpenGL.GLES2.NV.framebuffer_multisample import glRenderbufferStorageMultisampleNV
        rbo = one(glGenRenderbuffers(1)); glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorageMultisampleNV(GL_RENDERBUFFER, 4, GL_RGBA8, 8, 8)
        self.check_error('es nv framebuffer multisample')

    def test_nv_instanced_arrays(self):
        self.require_extension('GL_NV_instanced_arrays')
        from OpenGL.GLES2.NV.instanced_arrays import glVertexAttribDivisorNV
        vao = one(glGenVertexArrays(1)); glBindVertexArray(vao)
        glVertexAttribDivisorNV(0, 1)
        glBindVertexArray(0)
        self.check_error('es nv instanced arrays')

    def test_nv_internalformat_sample_query(self):
        self.require_extension('GL_NV_internalformat_sample_query')
        from OpenGL.GLES2.NV.internalformat_sample_query import (
            glGetInternalformatSampleivNV, GL_MULTISAMPLES_NV,
        )
        glGetInternalformatSampleivNV(GL_TEXTURE_2D_MULTISAMPLE, GL_RGBA8, 4,
                                      GL_MULTISAMPLES_NV, 1, np.zeros(1, 'i'))
        self.check_error('es nv internalformat sample query')

    def test_nv_polygon_mode(self):
        self.require_extension('GL_NV_polygon_mode')
        from OpenGL.GLES2.NV.polygon_mode import glPolygonModeNV, GL_LINE_NV, GL_FILL_NV
        glPolygonModeNV(GL_FRONT_AND_BACK, GL_LINE_NV)
        glPolygonModeNV(GL_FRONT_AND_BACK, GL_FILL_NV)
        self.check_error('es nv polygon mode')

    def test_nv_sample_locations(self):
        self.require_extension('GL_NV_sample_locations')
        from OpenGL.GLES2.NV.sample_locations import (
            glFramebufferSampleLocationsfvNV, glNamedFramebufferSampleLocationsfvNV,
            glResolveDepthValuesNV,
        )
        fbo = self._color_fbo()
        loc = np.array([0.5, 0.5], 'f')
        glFramebufferSampleLocationsfvNV(GL_FRAMEBUFFER, 0, 1, loc)
        glNamedFramebufferSampleLocationsfvNV(fbo, 0, 1, loc)
        glResolveDepthValuesNV()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('es nv sample locations')

    def test_nv_scissor_exclusive(self):
        self.require_extension('GL_NV_scissor_exclusive')
        from OpenGL.GLES2.NV.scissor_exclusive import (
            glScissorExclusiveNV, glScissorExclusiveArrayvNV, GL_SCISSOR_TEST_EXCLUSIVE_NV,
        )
        glEnable(GL_SCISSOR_TEST_EXCLUSIVE_NV)
        glScissorExclusiveNV(0, 0, 4, 4)
        glScissorExclusiveArrayvNV(0, 1, np.array([0, 0, 4, 4], 'i'))
        glDisable(GL_SCISSOR_TEST_EXCLUSIVE_NV)
        self.check_error('es nv scissor exclusive')

    def test_nv_viewport_swizzle(self):
        self.require_extension('GL_NV_viewport_swizzle')
        from OpenGL.GLES2.NV.viewport_swizzle import (
            glViewportSwizzleNV, GL_VIEWPORT_SWIZZLE_POSITIVE_X_NV,
            GL_VIEWPORT_SWIZZLE_POSITIVE_Y_NV, GL_VIEWPORT_SWIZZLE_POSITIVE_Z_NV,
            GL_VIEWPORT_SWIZZLE_POSITIVE_W_NV,
        )
        glViewportSwizzleNV(0, GL_VIEWPORT_SWIZZLE_POSITIVE_X_NV,
                            GL_VIEWPORT_SWIZZLE_POSITIVE_Y_NV,
                            GL_VIEWPORT_SWIZZLE_POSITIVE_Z_NV,
                            GL_VIEWPORT_SWIZZLE_POSITIVE_W_NV)
        self.check_error('es nv viewport swizzle')

    def test_nv_non_square_matrices(self):
        self.require_extension('GL_NV_non_square_matrices')
        from OpenGL.GLES2.NV.non_square_matrices import (
            glUniformMatrix2x3fvNV, glUniformMatrix3x2fvNV, glUniformMatrix2x4fvNV,
            glUniformMatrix4x2fvNV, glUniformMatrix3x4fvNV, glUniformMatrix4x3fvNV,
        )
        from OpenGL.GLES2 import shaders
        program = shaders.compileProgram(
            shaders.compileShader(
                '#version 300 es\n'
                '#extension GL_NV_non_square_matrices : require\n'
                'uniform mat2x3 a; uniform mat3x2 b; uniform mat2x4 c;\n'
                'uniform mat4x2 d; uniform mat3x4 e; uniform mat4x3 f;\n'
                'void main(){ gl_Position = vec4(a[0][0] + b[0][0] + c[0][0]\n'
                ' + d[0][0] + e[0][0] + f[0][0]); }',
                GL_VERTEX_SHADER),
            shaders.compileShader(
                '#version 300 es\nprecision mediump float; out vec4 o; void main(){ o = vec4(1.0); }',
                GL_FRAGMENT_SHADER),
            validate=False)
        glUseProgram(program)

        def L(n):
            return glGetUniformLocation(program, n)
        glUniformMatrix2x3fvNV(L('a'), 1, False, np.zeros((2, 3), 'f'))
        glUniformMatrix3x2fvNV(L('b'), 1, False, np.zeros((3, 2), 'f'))
        glUniformMatrix2x4fvNV(L('c'), 1, False, np.zeros((2, 4), 'f'))
        glUniformMatrix4x2fvNV(L('d'), 1, False, np.zeros((4, 2), 'f'))
        glUniformMatrix3x4fvNV(L('e'), 1, False, np.zeros((3, 4), 'f'))
        glUniformMatrix4x3fvNV(L('f'), 1, False, np.zeros((4, 3), 'f'))
        glUseProgram(0)
        self.check_error('es nv non square matrices')

    def test_nv_viewport_array(self):
        self.require_extension('GL_NV_viewport_array')
        from OpenGL.GLES2.NV.viewport_array import (
            glViewportArrayvNV, glViewportIndexedfNV, glViewportIndexedfvNV,
            glScissorArrayvNV, glScissorIndexedNV, glScissorIndexedvNV,
            glDepthRangeArrayfvNV, glDepthRangeIndexedfNV, glEnableiNV, glDisableiNV,
            glIsEnablediNV, glGetFloati_vNV, GL_VIEWPORT,
        )
        glViewportArrayvNV(0, 1, np.array([0, 0, 8, 8], 'f'))
        glViewportIndexedfNV(0, 0, 0, 8, 8)
        glViewportIndexedfvNV(0, np.array([0, 0, 8, 8], 'f'))
        glScissorArrayvNV(0, 1, np.array([0, 0, 8, 8], 'i'))
        glScissorIndexedNV(0, 0, 0, 8, 8)
        glScissorIndexedvNV(0, np.array([0, 0, 8, 8], 'i'))
        glDepthRangeArrayfvNV(0, 1, np.array([0.0, 1.0], 'f'))
        glDepthRangeIndexedfNV(0, 0.0, 1.0)
        glEnableiNV(GL_SCISSOR_TEST, 0)
        self.assertTrue(glIsEnablediNV(GL_SCISSOR_TEST, 0))
        glDisableiNV(GL_SCISSOR_TEST, 0)
        glGetFloati_vNV(GL_VIEWPORT, 0, np.zeros(4, 'f'))
        self.check_error('es nv viewport array')


if __name__ == '__main__':
    unittest.main()
