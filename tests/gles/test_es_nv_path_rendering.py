#! /usr/bin/env python3
"""GL_NV_path_rendering on OpenGL-ES: resolution-independent 2D path filling /
stroking (the same API surface as the desktop extension).

Functional tests -- build real path objects, set/query their parameters, drive
the path matrix stack, and stencil/cover them into a stencil framebuffer.  The
glyph *index* entry points need a real font file (absent headless) and so are
not exercised.
"""

import unittest
from arraycompat import np, one, ravel  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import *  # noqa: F401,F403
from OpenGL.GLES2.NV.path_rendering import *  # noqa: F401,F403

CMDS = np.array([GL_MOVE_TO_NV, GL_LINE_TO_NV, GL_LINE_TO_NV, GL_CLOSE_PATH_NV], 'u1')
COORDS = np.array([0.0, 0.0, 6.0, 0.0, 3.0, 6.0], 'f')


class TestESNVPathRendering(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def _stencil_fbo(self, w=16, h=16):
        color = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, color)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, w, h)
        ds = one(glGenRenderbuffers(1))
        glBindRenderbuffer(GL_RENDERBUFFER, ds)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, w, h)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, ds)
        glViewport(0, 0, w, h)
        return fbo

    def _make_path(self):
        p = one(glGenPathsNV(1))
        glPathCommandsNV(p, 4, CMDS, 6, GL_FLOAT, COORDS)
        return p

    def test_path_core(self):
        self.require_extension('GL_NV_path_rendering')
        p = self._make_path()
        self.assertTrue(glIsPathNV(p))
        svg = one(glGenPathsNV(1))
        s = b'M0,0 L6,0 L3,6 Z'
        glPathStringNV(svg, GL_PATH_FORMAT_SVG_NV, len(s), s)
        glPathSubCommandsNV(p, 0, 0, 1, np.array([GL_MOVE_TO_NV], 'u1'), 2, GL_FLOAT, np.array([0.0, 0.0], 'f'))
        glPathSubCoordsNV(p, 0, 2, GL_FLOAT, np.array([0.5, 0.5], 'f'))
        glPathParameterfNV(p, GL_PATH_STROKE_WIDTH_NV, 1.5)
        glPathParameteriNV(p, GL_PATH_JOIN_STYLE_NV, GL_ROUND_NV)
        glPathParameterfvNV(p, GL_PATH_STROKE_WIDTH_NV, np.array([1.5], 'f'))
        glPathParameterivNV(p, GL_PATH_JOIN_STYLE_NV, np.array([GL_ROUND_NV], 'i'))
        glPathDashArrayNV(p, 2, np.array([2.0, 1.0], 'f'))
        copy = one(glGenPathsNV(1)); glCopyPathNV(copy, p)
        weighted = one(glGenPathsNV(1))
        glWeightPathsNV(weighted, 2, np.array([p, copy], 'u4'), np.array([0.5, 0.5], 'f'))
        interp = one(glGenPathsNV(1)); glInterpolatePathsNV(interp, p, copy, 0.5)
        glTransformPathNV(copy, p, GL_TRANSLATE_X_NV, np.array([1.0], 'f'))
        glGetPathParameterfvNV(p, GL_PATH_STROKE_WIDTH_NV, np.zeros(1, 'f'))
        glGetPathParameterivNV(p, GL_PATH_JOIN_STYLE_NV, np.zeros(1, 'i'))
        glGetPathCommandsNV(p, np.zeros(8, 'u1'))
        glGetPathCoordsNV(p, np.zeros(16, 'f'))
        glGetPathDashArrayNV(p, np.zeros(2, 'f'))
        self.assertGreaterEqual(float(glGetPathLengthNV(p, 0, 4)), 0.0)
        glIsPointInFillPathNV(p, 0xFF, 1.0, 1.0)
        glIsPointInStrokePathNV(p, 1.0, 1.0)
        glDeletePathsNV(svg, 1)
        glDeletePathsNV(p, 1)
        self.check_error('es nv path rendering core')

    def test_path_matrices(self):
        self.require_extension('GL_NV_path_rendering')
        m = GL_PATH_MODELVIEW_NV
        ident = ravel(np.eye(4, dtype='f'))
        identd = ravel(np.eye(4, dtype='d'))
        glMatrixLoadIdentityEXT(GL_PATH_PROJECTION_NV)
        glMatrixOrthoEXT(GL_PATH_PROJECTION_NV, 0, 16, 0, 16, -1, 1)
        glMatrixFrustumEXT(GL_PATH_PROJECTION_NV, -1, 1, -1, 1, 1, 10)
        glMatrixLoadIdentityEXT(m)
        glMatrixLoadfEXT(m, ident); glMatrixLoaddEXT(m, identd)
        glMatrixLoadTransposefEXT(m, ident); glMatrixLoadTransposedEXT(m, identd)
        glMatrixMultfEXT(m, ident); glMatrixMultdEXT(m, identd)
        glMatrixMultTransposefEXT(m, ident); glMatrixMultTransposedEXT(m, identd)
        glMatrixTranslatefEXT(m, 1, 2, 0); glMatrixTranslatedEXT(m, 1, 2, 0)
        glMatrixScalefEXT(m, 2, 2, 1); glMatrixScaledEXT(m, 2, 2, 1)
        glMatrixRotatefEXT(m, 90, 0, 0, 1); glMatrixRotatedEXT(m, 90, 0, 0, 1)
        glMatrixPushEXT(m); glMatrixPopEXT(m)
        glMatrixLoad3x2fNV(m, np.zeros(6, 'f')); glMatrixLoad3x3fNV(m, np.zeros(9, 'f'))
        glMatrixLoadTranspose3x3fNV(m, np.zeros(9, 'f'))
        glMatrixMult3x2fNV(m, np.zeros(6, 'f')); glMatrixMult3x3fNV(m, np.zeros(9, 'f'))
        glMatrixMultTranspose3x3fNV(m, np.zeros(9, 'f'))
        glMatrixLoadIdentityEXT(m)
        self.check_error('es nv path rendering matrices')

    def test_path_stencil_cover(self):
        self.require_extension('GL_NV_path_rendering')
        self._stencil_fbo()
        glMatrixLoadIdentityEXT(GL_PATH_PROJECTION_NV)
        glMatrixOrthoEXT(GL_PATH_PROJECTION_NV, 0, 16, 0, 16, -1, 1)
        glMatrixLoadIdentityEXT(GL_PATH_MODELVIEW_NV)
        p = self._make_path()
        paths = np.array([p], 'u4')
        glPathStencilFuncNV(GL_ALWAYS, 0, 0xFF)
        glPathStencilDepthOffsetNV(0.0, 0.0)
        glPathCoverDepthFuncNV(GL_ALWAYS)
        glStencilFillPathNV(p, GL_COUNT_UP_NV, 0xFF)
        glCoverFillPathNV(p, GL_BOUNDING_BOX_NV)
        glStencilStrokePathNV(p, 1, 0xFF)
        glCoverStrokePathNV(p, GL_CONVEX_HULL_NV)
        glStencilThenCoverFillPathNV(p, GL_COUNT_UP_NV, 0xFF, GL_BOUNDING_BOX_NV)
        glStencilThenCoverStrokePathNV(p, 1, 0xFF, GL_CONVEX_HULL_NV)
        glStencilFillPathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, GL_COUNT_UP_NV, 0xFF, GL_NONE, None)
        glCoverFillPathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, GL_BOUNDING_BOX_NV, GL_NONE, None)
        glStencilStrokePathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, 1, 0xFF, GL_NONE, None)
        glCoverStrokePathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, GL_CONVEX_HULL_NV, GL_NONE, None)
        glStencilThenCoverFillPathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, GL_COUNT_UP_NV, 0xFF, GL_BOUNDING_BOX_NV, GL_NONE, None)
        glStencilThenCoverStrokePathInstancedNV(1, GL_UNSIGNED_INT, paths, 0, 1, 0xFF, GL_CONVEX_HULL_NV, GL_NONE, None)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('es nv path rendering stencil/cover')

    def test_path_metrics(self):
        self.require_extension('GL_NV_path_rendering')
        p = self._make_path()
        paths = np.array([p, p], 'u4')
        mask = GL_GLYPH_WIDTH_BIT_NV | GL_GLYPH_HEIGHT_BIT_NV
        glGetPathMetricsNV(mask, 2, GL_UNSIGNED_INT, paths, 0, 0, np.zeros(4, 'f'))
        glGetPathMetricRangeNV(mask, p, 1, 0, np.zeros(2, 'f'))
        glGetPathSpacingNV(GL_ACCUM_ADJACENT_PAIRS_NV, 2, GL_UNSIGNED_INT, paths, 0,
                           1.0, 1.0, GL_TRANSLATE_X_NV, np.zeros(2, 'f'))
        glPointAlongPathNV(p, 0, 4, 1.0, np.zeros(1, 'f'), np.zeros(1, 'f'),
                           np.zeros(1, 'f'), np.zeros(1, 'f'))
        self.check_error('es nv path rendering metrics')

    def test_path_gen(self):
        self.require_extension('GL_NV_path_rendering')
        coeffs = np.zeros((2, 3), 'f')
        glPathColorGenNV(GL_PRIMARY_COLOR, GL_PATH_OBJECT_BOUNDING_BOX_NV, GL_RGBA, np.zeros((4, 3), 'f'))
        glPathTexGenNV(GL_TEXTURE0, GL_PATH_OBJECT_BOUNDING_BOX_NV, 2, coeffs)
        glGetPathColorGenfvNV(GL_PRIMARY_COLOR, GL_PATH_GEN_MODE_NV, np.zeros(4, 'f'))
        glGetPathColorGenivNV(GL_PRIMARY_COLOR, GL_PATH_GEN_MODE_NV, np.zeros(4, 'i'))
        glGetPathTexGenfvNV(GL_TEXTURE0, GL_PATH_GEN_MODE_NV, np.zeros(4, 'f'))
        glGetPathTexGenivNV(GL_TEXTURE0, GL_PATH_GEN_MODE_NV, np.zeros(4, 'i'))

        from OpenGL.GLES2 import shaders
        vs = shaders.compileShader(
            '#version 320 es\nlayout(location=0) out vec2 tc;\n'
            'void main(){ tc = vec2(0.0); gl_Position = vec4(0.0); }', GL_VERTEX_SHADER)
        fs = shaders.compileShader(
            '#version 320 es\nprecision mediump float;\n'
            'layout(location=0) in vec2 tc; out vec4 c;\n'
            'void main(){ c = vec4(tc, 0.0, 1.0); }', GL_FRAGMENT_SHADER)
        program = glCreateProgram()
        glAttachShader(program, vs); glAttachShader(program, fs)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            self.skipTest('path fragment-input program did not link')
        idx = one(glGetProgramResourceIndex(program, GL_FRAGMENT_INPUT_NV, b'tc'))
        glProgramPathFragmentInputGenNV(program, 0, GL_OBJECT_LINEAR_NV, 2, np.zeros((2, 3), 'f'))
        glGetProgramResourcefvNV(program, GL_FRAGMENT_INPUT_NV, idx, 1,
                                 np.array([GL_PATH_GEN_COEFF_NV], 'u4'), 4,
                                 np.zeros(1, 'i'), np.zeros(4, 'f'))
        self.check_error('es nv path rendering gen')

    def test_path_glyphs(self):
        self.require_extension('GL_NV_path_rendering')
        from OpenGL import error
        base = int(glGenPathsNV(256))
        try:
            glPathGlyphRangeNV(base, GL_STANDARD_FONT_NAME_NV, b'Sans', 0, 0, 256,
                               GL_SKIP_MISSING_GLYPH_NV, 0, 64.0)
        except error.GLError:
            self.skipTest('no usable font for NV_path_rendering glyphs on this host')
        if glGetError() != GL_NO_ERROR:
            self.skipTest('no usable font for NV_path_rendering glyphs on this host')
        glPathGlyphsNV(base, GL_STANDARD_FONT_NAME_NV, b'Sans', 0, 2, GL_UNSIGNED_BYTE,
                       b'Hi', GL_SKIP_MISSING_GLYPH_NV, 0, 64.0)
        self.check_error('es nv path rendering glyphs')


if __name__ == '__main__':
    unittest.main()
