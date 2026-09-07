#! /usr/bin/env python3
"""GL 1.0 (compatibility): fixed-function state, clears, buffers, queries."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL1State(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_capabilities_and_blend(self):
        for cap in (
            GL_BLEND,
            GL_DEPTH_TEST,
            GL_STENCIL_TEST,
            GL_CULL_FACE,
            GL_LIGHTING,
            GL_TEXTURE_2D,
            GL_FOG,
            GL_NORMALIZE,
            GL_ALPHA_TEST,
            GL_SCISSOR_TEST,
            GL_COLOR_LOGIC_OP,
            GL_DITHER,
        ):
            glEnable(cap)
            self.assertTrue(glIsEnabled(cap))
            glDisable(cap)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glAlphaFunc(GL_GREATER, 0.1)
        glLogicOp(GL_COPY)
        self.check_error('caps/blend')

    def test_clears(self):
        glClearColor(0.0, 0.0, 0.25, 1.0)
        glClearDepth(1.0)
        glClearStencil(0)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClearIndex(0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        self.check_error('clears')

    def test_masks_and_funcs(self):
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glDepthMask(GL_TRUE)
        glDepthFunc(GL_LEQUAL)
        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilMask(0xFF)
        glIndexMask(0xFFFFFFFF)
        self.check_error('masks/funcs')

    def test_rasterization_state(self):
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glPolygonStipple(np.zeros(128, 'B'))
        stipple = glGetPolygonStipple()
        self.assertTrue(stipple is not None)
        glLineWidth(1.0)
        glLineStipple(1, 0xFFFF)
        glPointSize(1.0)
        glShadeModel(GL_SMOOTH)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glScissor(0, 0, self.width, self.height)
        self.check_error('rasterization state')

    def test_buffers_and_queries(self):
        # Named rather than assumed: this backend may be drawing into a
        # framebuffer object, which takes GL_COLOR_ATTACHMENTi and not
        # GL_BACK.
        glDrawBuffer(self.colour_buffer_name())
        glReadBuffer(self.colour_buffer_name())
        self.assertGreaterEqual(int(glGetIntegerv(GL_MAX_TEXTURE_SIZE)), 64)
        glGetBooleanv(GL_DEPTH_WRITEMASK, (ctypes.c_ubyte * 1)())
        glGetFloatv(GL_COLOR_CLEAR_VALUE, (ctypes.c_float * 4)())
        glGetDoublev(GL_DEPTH_CLEAR_VALUE, (ctypes.c_double * 1)())
        self.assertEqual(glGetError(), GL_NO_ERROR)
        glFlush()
        glFinish()
        self.check_error('buffers/queries')

    def test_attrib_stack(self):
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPopAttrib()
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)
        glPopClientAttrib()
        self.check_error('attrib stack')


if __name__ == '__main__':
    unittest.main()
