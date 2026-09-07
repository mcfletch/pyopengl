#! /usr/bin/env python3
"""State / rasterization extensions: blend variants, indexed blend, viewport
arrays, polygon-offset clamp, clip control, framebuffer attach, multiview."""

import unittest
from arraycompat import np, object_names

from egltestcase import ESTestCase
from OpenGL.GLES3 import (
    GL_BLEND,
    GL_FUNC_ADD,
    GL_FUNC_SUBTRACT,
    GL_ONE,
    GL_ZERO,
    GL_TRUE,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_TEXTURE_2D,
    GL_RGBA8,
    GL_COLOR_ATTACHMENT0 as ATTACH,
    glGenTextures,
    glBindTexture,
    glTexStorage2D,
    glGenFramebuffers,
    glBindFramebuffer,
)

from OpenGL.GLES2.EXT import blend_func_extended as bfe
from OpenGL.GLES2.EXT import blend_minmax as bmm
from OpenGL.GLES2.KHR import blend_equation_advanced as bea
from OpenGL.GLES2.EXT import geometry_shader as ext_geom
from OpenGL.GLES2.OES import geometry_shader as oes_geom
from OpenGL.GLES2.EXT import tessellation_shader as ext_tess
from OpenGL.GLES2.OES import tessellation_shader as oes_tess
from OpenGL.GLES2.OES import sample_shading as oes_ss
from OpenGL.GLES2.EXT import primitive_bounding_box as ext_pbb
from OpenGL.GLES2.OES import primitive_bounding_box as oes_pbb
from OpenGL.GLES2.EXT import polygon_offset_clamp as ext_poc
from OpenGL.GLES2.EXT import clip_control as ext_clip
from OpenGL.GLES2.OES import viewport_array as oes_vp
from OpenGL.GLES2.MESA import framebuffer_flip_y as mesa_flip
from OpenGL.GLES2.NV import texture_barrier as nv_barrier
from OpenGL.GLES2.OVR import multiview as ovr
from OpenGL.GLES2.EXT import shader_framebuffer_fetch_non_coherent as ext_fbf
from OpenGL.GLES2.NV import read_buffer as nv_read
from OpenGL.GLES2.EXT import draw_buffers_indexed as ext_dbi
from OpenGL.GLES2.OES import draw_buffers_indexed as oes_dbi
from OpenGL.GLES2.EXT import draw_buffers as ext_db
from OpenGL.GLES2.EXT.tessellation_shader import GL_PATCH_VERTICES_EXT
from OpenGL.GLES2.OES.tessellation_shader import GL_PATCH_VERTICES_OES
from OpenGL.GLES2.EXT.clip_control import GL_LOWER_LEFT_EXT, GL_ZERO_TO_ONE_EXT
from OpenGL.GLES2.MESA.framebuffer_flip_y import GL_FRAMEBUFFER_FLIP_Y_MESA
from OpenGL.GLES3 import GL_PROGRAM_OUTPUT, GL_VIEWPORT

VERTEX = '''#version 300 es
in vec4 p; out vec4 v; void main() { v = p; gl_Position = p; }'''
FRAGMENT = '''#version 300 es
precision mediump float;
in vec4 v; out vec4 c; void main() { c = v; }'''


class TestStateExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def _color_fbo(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        return tex

    def test_ext_blend_func_extended(self):
        self.require_extension('GL_EXT_blend_func_extended')
        with self.exercise():
            program = self.compile_program(VERTEX, FRAGMENT)
            bfe.glBindFragDataLocationEXT(program, 0, 'c')
            bfe.glBindFragDataLocationIndexedEXT(program, 0, 0, 'c')
            bfe.glGetFragDataIndexEXT(program, 'c')
            bfe.glGetProgramResourceLocationIndexEXT(program, GL_PROGRAM_OUTPUT, 'c')

    def test_ext_blend_minmax(self):
        self.require_extension('GL_EXT_blend_minmax')
        with self.exercise():
            bmm.glBlendEquationEXT(GL_FUNC_ADD)

    def test_khr_blend_equation_advanced(self):
        self.require_extension('GL_KHR_blend_equation_advanced')
        with self.exercise():
            bea.glBlendBarrierKHR()

    def test_geometry_shader_attach(self):
        self.require_extension('GL_EXT_geometry_shader')
        with self.exercise():
            tex = self._color_fbo()
            ext_geom.glFramebufferTextureEXT(GL_FRAMEBUFFER, ATTACH, tex, 0)

    def test_oes_geometry_shader_attach(self):
        self.require_extension('GL_OES_geometry_shader')
        with self.exercise():
            tex = self._color_fbo()
            oes_geom.glFramebufferTextureOES(GL_FRAMEBUFFER, ATTACH, tex, 0)

    def test_tessellation_patch(self):
        self.require_extension('GL_EXT_tessellation_shader')
        with self.exercise():
            ext_tess.glPatchParameteriEXT(GL_PATCH_VERTICES_EXT, 3)

    def test_oes_tessellation_patch(self):
        self.require_extension('GL_OES_tessellation_shader')
        with self.exercise():
            oes_tess.glPatchParameteriOES(GL_PATCH_VERTICES_OES, 3)

    def test_oes_sample_shading(self):
        self.require_extension('GL_OES_sample_shading')
        with self.exercise():
            oes_ss.glMinSampleShadingOES(1.0)

    def test_primitive_bounding_box(self):
        self.require_extension('GL_EXT_primitive_bounding_box')
        with self.exercise():
            ext_pbb.glPrimitiveBoundingBoxEXT(-1, -1, -1, 1, 1, 1, 1, 1)

    def test_oes_primitive_bounding_box(self):
        self.require_extension('GL_OES_primitive_bounding_box')
        with self.exercise():
            oes_pbb.glPrimitiveBoundingBoxOES(-1, -1, -1, 1, 1, 1, 1, 1)

    def test_ext_polygon_offset_clamp(self):
        self.require_extension('GL_EXT_polygon_offset_clamp')
        with self.exercise():
            ext_poc.glPolygonOffsetClampEXT(1.0, 1.0, 0.0)

    def test_ext_clip_control(self):
        self.require_extension('GL_EXT_clip_control')
        with self.exercise():
            ext_clip.glClipControlEXT(GL_LOWER_LEFT_EXT, GL_ZERO_TO_ONE_EXT)

    def test_oes_viewport_array(self):
        self.require_extension('GL_OES_viewport_array')
        with self.exercise():
            oes_vp.glViewportArrayvOES(0, 1, np.array([0, 0, 16, 16], 'f'))
            oes_vp.glViewportIndexedfOES(0, 0.0, 0.0, 16.0, 16.0)
            oes_vp.glViewportIndexedfvOES(0, np.array([0, 0, 16, 16], 'f'))
            oes_vp.glScissorArrayvOES(0, 1, np.array([0, 0, 16, 16], 'i'))
            oes_vp.glScissorIndexedOES(0, 0, 0, 16, 16)
            oes_vp.glScissorIndexedvOES(0, np.array([0, 0, 16, 16], 'i'))
            oes_vp.glDepthRangeArrayfvOES(0, 1, np.array([0.0, 1.0], 'f'))
            oes_vp.glDepthRangeIndexedfOES(0, 0.0, 1.0)
            oes_vp.glEnableiOES(GL_BLEND, 0)
            oes_vp.glIsEnablediOES(GL_BLEND, 0)
            oes_vp.glDisableiOES(GL_BLEND, 0)
            oes_vp.glGetFloati_vOES(GL_VIEWPORT, 0, np.zeros(4, 'f'))

    def test_mesa_framebuffer_flip_y(self):
        self.require_extension('GL_MESA_framebuffer_flip_y')
        with self.exercise():
            self._color_fbo()
            mesa_flip.glFramebufferParameteriMESA(
                GL_FRAMEBUFFER, GL_FRAMEBUFFER_FLIP_Y_MESA, GL_TRUE
            )
            mesa_flip.glGetFramebufferParameterivMESA(
                GL_FRAMEBUFFER, GL_FRAMEBUFFER_FLIP_Y_MESA, np.zeros(1, 'i')
            )

    def test_nv_texture_barrier(self):
        self.require_extension('GL_NV_texture_barrier')
        with self.exercise():
            nv_barrier.glTextureBarrierNV()

    def test_ovr_multiview(self):
        self.require_extension('GL_OVR_multiview')
        with self.exercise():
            from OpenGL.GLES3 import GL_TEXTURE_2D_ARRAY, glTexStorage3D

            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D_ARRAY, tex)
            glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 16, 16, 2)
            glBindFramebuffer(GL_FRAMEBUFFER, glGenFramebuffers(1))
            ovr.glFramebufferTextureMultiviewOVR(GL_FRAMEBUFFER, ATTACH, tex, 0, 0, 2)
            # the DSA form is unsupported in ES, so this fails GL validation; the
            # call still drives the wrapper -- exercise() tolerates the error
            ovr.glNamedFramebufferTextureMultiviewOVR(
                int(glGenFramebuffers(1)), ATTACH, tex, 0, 0, 2
            )

    def test_ext_shader_framebuffer_fetch(self):
        self.require_extension('GL_EXT_shader_framebuffer_fetch_non_coherent')
        with self.exercise():
            ext_fbf.glFramebufferFetchBarrierEXT()

    def test_nv_read_buffer(self):
        self.require_extension('GL_NV_read_buffer')
        with self.exercise():
            from OpenGL.GLES3 import GL_BACK

            nv_read.glReadBufferNV(GL_BACK)

    def test_ext_draw_buffers_indexed(self):
        self.require_extension('GL_EXT_draw_buffers_indexed')
        with self.exercise():
            ext_dbi.glEnableiEXT(GL_BLEND, 0)
            ext_dbi.glIsEnablediEXT(GL_BLEND, 0)
            ext_dbi.glBlendEquationiEXT(0, GL_FUNC_ADD)
            ext_dbi.glBlendEquationSeparateiEXT(0, GL_FUNC_ADD, GL_FUNC_SUBTRACT)
            ext_dbi.glBlendFunciEXT(0, GL_ONE, GL_ZERO)
            ext_dbi.glBlendFuncSeparateiEXT(0, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
            ext_dbi.glColorMaskiEXT(0, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
            ext_dbi.glDisableiEXT(GL_BLEND, 0)

    def test_oes_draw_buffers_indexed(self):
        self.require_extension('GL_OES_draw_buffers_indexed')
        with self.exercise():
            oes_dbi.glEnableiOES(GL_BLEND, 0)
            oes_dbi.glIsEnablediOES(GL_BLEND, 0)
            oes_dbi.glBlendEquationiOES(0, GL_FUNC_ADD)
            oes_dbi.glBlendEquationSeparateiOES(0, GL_FUNC_ADD, GL_FUNC_SUBTRACT)
            oes_dbi.glBlendFunciOES(0, GL_ONE, GL_ZERO)
            oes_dbi.glBlendFuncSeparateiOES(0, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
            oes_dbi.glColorMaskiOES(0, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
            oes_dbi.glDisableiOES(GL_BLEND, 0)

    def test_ext_draw_buffers(self):
        self.require_extension('GL_EXT_draw_buffers')
        with self.exercise():
            self._color_fbo()
            ext_db.glDrawBuffersEXT(1, object_names(GL_COLOR_ATTACHMENT0))


if __name__ == '__main__':
    unittest.main()
