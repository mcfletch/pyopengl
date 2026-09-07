#! /usr/bin/env python3
"""Legacy NVIDIA desktop-GL extensions: NV fences, NV occlusion queries, 64-bit
float depth range, point sprites, multisample-coverage renderbuffers/textures,
explicit multisample and NV transform-feedback objects.

Functional tests -- real objects and real calls with a clean error state.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestNVLegacyMisc(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    # --- GL_NV_fence -----------------------------------------------------
    def test_nv_fence(self):
        self.require_extension('GL_NV_fence')
        from OpenGL.GL.NV.fence import (
            glGenFencesNV, glDeleteFencesNV, glSetFenceNV, glTestFenceNV,
            glFinishFenceNV, glGetFenceivNV, glIsFenceNV,
            GL_ALL_COMPLETED_NV, GL_FENCE_STATUS_NV,
        )

        fences = np.zeros(1, 'u4')
        glGenFencesNV(1, fences)
        fence = int(fences[0])
        glSetFenceNV(fence, GL_ALL_COMPLETED_NV)
        self.assertTrue(glIsFenceNV(fence))
        glTestFenceNV(fence)
        glFinishFenceNV(fence)
        glGetFenceivNV(fence, GL_FENCE_STATUS_NV, np.zeros(1, 'i'))
        glDeleteFencesNV(1, fences)
        self.check_error('nv fence')

    # --- GL_NV_occlusion_query -------------------------------------------
    def test_nv_occlusion_query(self):
        self.require_extension('GL_NV_occlusion_query')
        from OpenGL.GL.NV.occlusion_query import (
            glGenOcclusionQueriesNV, glDeleteOcclusionQueriesNV,
            glBeginOcclusionQueryNV, glEndOcclusionQueryNV, glIsOcclusionQueryNV,
            glGetOcclusionQueryivNV, glGetOcclusionQueryuivNV, GL_PIXEL_COUNT_NV,
        )

        qs = np.zeros(1, 'u4')
        glGenOcclusionQueriesNV(1, qs)
        q = int(qs[0])
        glBeginOcclusionQueryNV(q)
        glEndOcclusionQueryNV()
        self.assertTrue(glIsOcclusionQueryNV(q))
        glGetOcclusionQueryivNV(q, GL_PIXEL_COUNT_NV, np.zeros(1, 'i'))
        glGetOcclusionQueryuivNV(q, GL_PIXEL_COUNT_NV, np.zeros(1, 'u4'))
        glDeleteOcclusionQueriesNV(1, qs)
        self.check_error('nv occlusion query')

    # --- GL_NV_depth_buffer_float ----------------------------------------
    def test_nv_depth_buffer_float(self):
        self.require_extension('GL_NV_depth_buffer_float')
        from OpenGL.GL.NV.depth_buffer_float import (
            glDepthRangedNV, glClearDepthdNV, glDepthBoundsdNV,
        )

        glDepthRangedNV(0.0, 1.0)
        glClearDepthdNV(1.0)
        glDepthBoundsdNV(0.0, 1.0)
        self.check_error('nv depth buffer float')

    # --- GL_NV_point_sprite ----------------------------------------------
    def test_nv_point_sprite(self):
        self.require_extension('GL_NV_point_sprite')
        from OpenGL.GL.NV.point_sprite import (
            glPointParameteriNV, glPointParameterivNV, GL_POINT_SPRITE_R_MODE_NV,
        )

        glPointParameteriNV(GL_POINT_SPRITE_R_MODE_NV, GL_ZERO)
        glPointParameterivNV(GL_POINT_SPRITE_R_MODE_NV, np.array([GL_ZERO], 'i'))
        self.check_error('nv point sprite')

    # --- GL_NV_framebuffer_multisample_coverage --------------------------
    def test_nv_framebuffer_multisample_coverage(self):
        self.require_extension('GL_NV_framebuffer_multisample_coverage')
        from OpenGL.GL.NV.framebuffer_multisample_coverage import (
            glRenderbufferStorageMultisampleCoverageNV,
        )

        rbo = one(glGenRenderbuffers(1))
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorageMultisampleCoverageNV(GL_RENDERBUFFER, 8, 4, GL_RGBA8, 8, 8)
        self.check_error('nv framebuffer multisample coverage')

    # --- GL_NV_explicit_multisample --------------------------------------
    def test_nv_explicit_multisample(self):
        self.require_extension('GL_NV_explicit_multisample')
        from OpenGL.GL.NV.explicit_multisample import (
            glGetMultisamplefvNV, glSampleMaskIndexedNV, glTexRenderbufferNV,
            GL_SAMPLE_POSITION_NV, GL_TEXTURE_RENDERBUFFER_NV,
        )

        rbo = one(glGenRenderbuffers(1))
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 4, GL_RGBA8, 8, 8)
        # sample-position query reads the bound multisample draw framebuffer
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rbo)
        glGetMultisamplefvNV(GL_SAMPLE_POSITION_NV, 0, np.zeros(2, 'f'))
        glSampleMaskIndexedNV(0, 0xFF)
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_RENDERBUFFER_NV, tex)
        glTexRenderbufferNV(GL_TEXTURE_RENDERBUFFER_NV, rbo)
        self.check_error('nv explicit multisample')

    # --- GL_NV_texture_multisample ---------------------------------------
    def test_nv_texture_multisample(self):
        self.require_extension('GL_NV_texture_multisample')
        from OpenGL.GL.NV.texture_multisample import (
            glTexImage2DMultisampleCoverageNV, glTexImage3DMultisampleCoverageNV,
            glTextureImage2DMultisampleNV, glTextureImage2DMultisampleCoverageNV,
            glTextureImage3DMultisampleNV, glTextureImage3DMultisampleCoverageNV,
        )

        t = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, t)
        glTexImage2DMultisampleCoverageNV(GL_TEXTURE_2D_MULTISAMPLE, 8, 4, GL_RGBA8, 8, 8, GL_TRUE)
        ta = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, ta)
        glTexImage3DMultisampleCoverageNV(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 8, 4, GL_RGBA8, 8, 8, 2, GL_TRUE)

        d2 = one(glGenTextures(1))
        glTextureImage2DMultisampleNV(d2, GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 8, 8, GL_TRUE)
        d2c = one(glGenTextures(1))
        glTextureImage2DMultisampleCoverageNV(d2c, GL_TEXTURE_2D_MULTISAMPLE, 8, 4, GL_RGBA8, 8, 8, GL_TRUE)
        d3 = one(glGenTextures(1))
        glTextureImage3DMultisampleNV(d3, GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 8, 8, 2, GL_TRUE)
        d3c = one(glGenTextures(1))
        glTextureImage3DMultisampleCoverageNV(d3c, GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 8, 4, GL_RGBA8, 8, 8, 2, GL_TRUE)
        self.check_error('nv texture multisample')

    # --- GL_NV_transform_feedback2 ---------------------------------------
    def test_nv_transform_feedback2(self):
        self.require_extension('GL_NV_transform_feedback2')
        from OpenGL.GL.NV.transform_feedback2 import (
            glGenTransformFeedbacksNV, glDeleteTransformFeedbacksNV,
            glBindTransformFeedbackNV, glIsTransformFeedbackNV,
            glPauseTransformFeedbackNV, glResumeTransformFeedbackNV,
            glDrawTransformFeedbackNV,
        )
        from OpenGL.GL import shaders

        program = shaders.compileProgram(
            shaders.compileShader(
                '#version 150\nout float v; void main(){ v = 1.0; gl_Position = vec4(0.0); }',
                GL_VERTEX_SHADER,
            ),
            shaders.compileShader(
                '#version 150\nout vec4 c; void main(){ c = vec4(1.0); }',
                GL_FRAGMENT_SHADER,
            ),
            validate=False,
        )
        glTransformFeedbackVaryings(program, 1, _char_pp(['v']), GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(program)
        glUseProgram(program)

        tfs = np.zeros(1, 'u4')
        glGenTransformFeedbacksNV(1, tfs)
        tf = int(tfs[0])
        glBindTransformFeedbackNV(GL_TRANSFORM_FEEDBACK, tf)
        self.assertTrue(glIsTransformFeedbackNV(tf))
        tbo = one(glGenBuffers(1))
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, tbo)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 64, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)

        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_POINTS)
        glPauseTransformFeedbackNV()
        glResumeTransformFeedbackNV()
        glEndTransformFeedback()
        glDrawTransformFeedbackNV(GL_POINTS, tf)
        glDisable(GL_RASTERIZER_DISCARD)

        glBindTransformFeedbackNV(GL_TRANSFORM_FEEDBACK, 0)
        glDeleteTransformFeedbacksNV(1, tfs)
        glUseProgram(0)
        self.check_error('nv transform feedback2')


if __name__ == '__main__':
    unittest.main()
