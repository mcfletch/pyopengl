#! /usr/bin/env python3
"""NVIDIA desktop-GL state / rasterization extensions: conditional render (NVX),
bindless texture/image handles (NV), advanced blend, clip-space W scaling,
conservative raster (+ dilate / pre-snap), draw-texture, fragment coverage to
colour, mixed-sample coverage modulation, internalformat sample query, sample
locations, exclusive scissor, viewport swizzle and the shading-rate image.

Functional tests -- real objects and real calls with a clean error state.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403


class TestNVState(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def _color_fbo(self, fmt=GL_RGBA8, w=8, h=8):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, fmt, w, h)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        return fbo, tex

    # --- GL_NVX_conditional_render ---------------------------------------
    def test_nvx_conditional_render(self):
        self.require_extension('GL_NVX_conditional_render')
        from OpenGL.GL.NVX.conditional_render import (
            glBeginConditionalRenderNVX, glEndConditionalRenderNVX,
        )

        q = one(glGenQueries(1))
        glBeginQuery(GL_SAMPLES_PASSED, q)
        glEndQuery(GL_SAMPLES_PASSED)
        glBeginConditionalRenderNVX(q)
        glEndConditionalRenderNVX()
        self.check_error('nvx conditional render')

    # --- GL_NV_bindless_texture ------------------------------------------
    def test_nv_bindless_texture(self):
        self.require_extension('GL_NV_bindless_texture')
        from OpenGL.GL.NV.bindless_texture import (
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

        program = self.compile_program(
            '#version 450 core\nvoid main(){gl_Position=vec4(0.0);}',
            '#version 450 core\n'
            '#extension GL_NV_bindless_texture : require\n'
            'uniform sampler2D s; out vec4 c;\n'
            'void main(){ c = texture(s, vec2(0.5)); }',
        )
        loc = glGetUniformLocation(program, 's')
        glUseProgram(program)
        glUniformHandleui64NV(loc, handle)
        glUniformHandleui64vNV(loc, 1, np.array([handle], 'uint64'))
        glProgramUniformHandleui64NV(program, loc, handle)
        glProgramUniformHandleui64vNV(program, loc, 1, np.array([handle], 'uint64'))
        glUseProgram(0)
        glMakeTextureHandleNonResidentNV(handle)
        self.check_error('nv bindless texture')

    # --- GL_NV_blend_equation_advanced -----------------------------------
    def test_nv_blend_equation_advanced(self):
        self.require_extension('GL_NV_blend_equation_advanced')
        from OpenGL.GL.NV.blend_equation_advanced import (
            glBlendBarrierNV, glBlendParameteriNV,
            GL_BLEND_OVERLAP_NV, GL_CONJOINT_NV, GL_BLEND_PREMULTIPLIED_SRC_NV,
        )

        glBlendParameteriNV(GL_BLEND_OVERLAP_NV, GL_CONJOINT_NV)
        glBlendParameteriNV(GL_BLEND_PREMULTIPLIED_SRC_NV, GL_TRUE)
        glBlendBarrierNV()
        self.check_error('nv blend equation advanced')

    # --- GL_NV_clip_space_w_scaling --------------------------------------
    def test_nv_clip_space_w_scaling(self):
        self.require_extension('GL_NV_clip_space_w_scaling')
        from OpenGL.GL.NV.clip_space_w_scaling import glViewportPositionWScaleNV

        glViewportPositionWScaleNV(0, 1.0, 1.0)
        self.check_error('nv clip space w scaling')

    # --- GL_NV_conservative_raster (+ dilate / pre-snap) -----------------
    def test_nv_conservative_raster(self):
        self.require_extension('GL_NV_conservative_raster')
        from OpenGL.GL.NV.conservative_raster import glSubpixelPrecisionBiasNV

        glSubpixelPrecisionBiasNV(4, 4)
        glSubpixelPrecisionBiasNV(0, 0)
        self.check_error('nv conservative raster')

    def test_nv_conservative_raster_dilate(self):
        self.require_extension('GL_NV_conservative_raster_dilate')
        from OpenGL.GL.NV.conservative_raster_dilate import (
            glConservativeRasterParameterfNV, GL_CONSERVATIVE_RASTER_DILATE_NV,
        )

        glConservativeRasterParameterfNV(GL_CONSERVATIVE_RASTER_DILATE_NV, 0.5)
        self.check_error('nv conservative raster dilate')

    def test_nv_conservative_raster_pre_snap_triangles(self):
        self.require_extension('GL_NV_conservative_raster_pre_snap_triangles')
        from OpenGL.GL.NV.conservative_raster_pre_snap_triangles import (
            glConservativeRasterParameteriNV, GL_CONSERVATIVE_RASTER_MODE_NV,
            GL_CONSERVATIVE_RASTER_MODE_POST_SNAP_NV,
        )

        glConservativeRasterParameteriNV(
            GL_CONSERVATIVE_RASTER_MODE_NV, GL_CONSERVATIVE_RASTER_MODE_POST_SNAP_NV
        )
        self.check_error('nv conservative raster pre snap triangles')

    # --- GL_NV_draw_texture ----------------------------------------------
    def test_nv_draw_texture(self):
        self.require_extension('GL_NV_draw_texture')
        from OpenGL.GL.NV.draw_texture import glDrawTextureNV

        self._color_fbo()
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glDrawTextureNV(tex, 0, 0.0, 0.0, 8.0, 8.0, 0.0, 0.0, 0.0, 1.0, 1.0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('nv draw texture')

    # --- GL_NV_fragment_coverage_to_color --------------------------------
    def test_nv_fragment_coverage_to_color(self):
        self.require_extension('GL_NV_fragment_coverage_to_color')
        from OpenGL.GL.NV.fragment_coverage_to_color import (
            glFragmentCoverageColorNV, GL_FRAGMENT_COVERAGE_TO_COLOR_NV,
        )

        fbo, _ = self._color_fbo(fmt=GL_R32UI)
        glFragmentCoverageColorNV(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('nv fragment coverage to color')

    # --- GL_NV_framebuffer_mixed_samples ---------------------------------
    def test_nv_framebuffer_mixed_samples(self):
        self.require_extension('GL_NV_framebuffer_mixed_samples')
        from OpenGL.GL.NV.framebuffer_mixed_samples import (
            glCoverageModulationNV, glCoverageModulationTableNV,
            glGetCoverageModulationTableNV, GL_COVERAGE_MODULATION_TABLE_SIZE_NV,
        )
        from OpenGL.GL.EXT.raster_multisample import glRasterSamplesEXT

        glRasterSamplesEXT(4, GL_TRUE)
        glCoverageModulationNV(GL_RGBA)
        size = int(self.getInteger(GL_COVERAGE_MODULATION_TABLE_SIZE_NV))
        if size > 0:
            table = np.array([1.0] * size, 'f')
            glCoverageModulationTableNV(size, table)
            glGetCoverageModulationTableNV(size, np.zeros(size, 'f'))
        glRasterSamplesEXT(0, GL_FALSE)
        glCoverageModulationNV(GL_NONE)
        self.check_error('nv framebuffer mixed samples')

    # --- GL_NV_internalformat_sample_query -------------------------------
    def test_nv_internalformat_sample_query(self):
        self.require_extension('GL_NV_internalformat_sample_query')
        from OpenGL.GL.NV.internalformat_sample_query import (
            glGetInternalformatSampleivNV, GL_MULTISAMPLES_NV,
        )

        glGetInternalformatSampleivNV(
            GL_TEXTURE_2D_MULTISAMPLE, GL_RGBA8, 4, GL_MULTISAMPLES_NV,
            1, np.zeros(1, 'i'),
        )
        self.check_error('nv internalformat sample query')

    # --- GL_NV_sample_locations ------------------------------------------
    def test_nv_sample_locations(self):
        self.require_extension('GL_NV_sample_locations')
        from OpenGL.GL.NV.sample_locations import (
            glFramebufferSampleLocationsfvNV, glNamedFramebufferSampleLocationsfvNV,
            glResolveDepthValuesNV,
        )

        fbo, _ = self._color_fbo()
        locations = np.array([0.5, 0.5], 'f')
        glFramebufferSampleLocationsfvNV(GL_FRAMEBUFFER, 0, 1, locations)
        glNamedFramebufferSampleLocationsfvNV(fbo, 0, 1, locations)
        glResolveDepthValuesNV()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('nv sample locations')

    # --- GL_NV_scissor_exclusive -----------------------------------------
    def test_nv_scissor_exclusive(self):
        self.require_extension('GL_NV_scissor_exclusive')
        from OpenGL.GL.NV.scissor_exclusive import (
            glScissorExclusiveNV, glScissorExclusiveArrayvNV,
            GL_SCISSOR_TEST_EXCLUSIVE_NV,
        )

        glEnable(GL_SCISSOR_TEST_EXCLUSIVE_NV)
        glScissorExclusiveNV(0, 0, 4, 4)
        glScissorExclusiveArrayvNV(0, 1, np.array([0, 0, 4, 4], 'i'))
        glDisable(GL_SCISSOR_TEST_EXCLUSIVE_NV)
        self.check_error('nv scissor exclusive')

    # --- GL_NV_viewport_swizzle ------------------------------------------
    def test_nv_viewport_swizzle(self):
        self.require_extension('GL_NV_viewport_swizzle')
        from OpenGL.GL.NV.viewport_swizzle import (
            glViewportSwizzleNV,
            GL_VIEWPORT_SWIZZLE_POSITIVE_X_NV, GL_VIEWPORT_SWIZZLE_POSITIVE_Y_NV,
            GL_VIEWPORT_SWIZZLE_POSITIVE_Z_NV, GL_VIEWPORT_SWIZZLE_POSITIVE_W_NV,
        )

        glViewportSwizzleNV(
            0,
            GL_VIEWPORT_SWIZZLE_POSITIVE_X_NV, GL_VIEWPORT_SWIZZLE_POSITIVE_Y_NV,
            GL_VIEWPORT_SWIZZLE_POSITIVE_Z_NV, GL_VIEWPORT_SWIZZLE_POSITIVE_W_NV,
        )
        self.check_error('nv viewport swizzle')

    # --- GL_NV_shading_rate_image ----------------------------------------
    def test_nv_shading_rate_image(self):
        self.require_extension('GL_NV_shading_rate_image')
        from OpenGL.GL.NV.shading_rate_image import (
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
        palette = np.array(
            [GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV] * psize, 'u4'
        )
        glShadingRateImagePaletteNV(0, 0, psize, palette)
        glGetShadingRateImagePaletteNV(0, 0, np.zeros(1, 'u4'))
        glShadingRateSampleOrderNV(GL_SHADING_RATE_SAMPLE_ORDER_DEFAULT_NV)
        glGetShadingRateSampleLocationivNV(
            GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV, 0, 0, np.zeros(3, 'i')
        )
        glBindShadingRateImageNV(0)
        self.check_error('nv shading rate image')


if __name__ == '__main__':
    unittest.main()
