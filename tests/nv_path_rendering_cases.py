#! /usr/bin/env python3
"""GL_NV_path_rendering, which desktop GL and OpenGL-ES offer alike.

The extension is one API and the two suites asked the same questions of it in
two files that had drifted apart in formatting rather than in substance.  The
questions live here; ``gl/test_ext_nv_path_rendering.py`` and
``gles/test_es_nv_path_rendering.py`` say which context to ask them in and
which module the entry points come from.

The entry points are reached through ``self.nv`` rather than by importing them
here, because the two APIs bind them from different libraries:
``OpenGL.GL.NV.path_rendering`` and ``OpenGL.GLES2.NV.path_rendering`` are
separate objects, and a name alone does not say which.
"""

from arraycompat import np, one, ravel


#: The coordinates of a closed triangle; the commands that walk it are built
#: per API by :meth:`NVPathRenderingMixin.commands`, since the enums are named
#: on the extension module rather than here.
COORDS = np.array([0.0, 0.0, 6.0, 0.0, 3.0, 6.0], 'f')


class NVPathRenderingMixin(object):
    """The cases, over whichever API the concrete class supplies.

    A subclass sets :attr:`nv` to the ``path_rendering`` module for its API and
    inherits from its suite's base case.
    """

    #: The API's ``NV.path_rendering`` module; set by the concrete class.
    nv = None

    def commands(self):
        """The path commands for :data:`COORDS`, as this API names them."""
        return np.array(
            [
                self.nv.GL_MOVE_TO_NV,
                self.nv.GL_LINE_TO_NV,
                self.nv.GL_LINE_TO_NV,
                self.nv.GL_CLOSE_PATH_NV,
            ],
            'u1',
        )

    def _stencil_fbo(self, w=16, h=16):
        color = one(self.gl.glGenTextures(1))
        self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, color)
        self.gl.glTexStorage2D(self.gl.GL_TEXTURE_2D, 1, self.gl.GL_RGBA8, w, h)
        ds = one(self.gl.glGenRenderbuffers(1))
        self.gl.glBindRenderbuffer(self.gl.GL_RENDERBUFFER, ds)
        self.gl.glRenderbufferStorage(self.gl.GL_RENDERBUFFER, self.gl.GL_DEPTH24_STENCIL8, w, h)
        fbo = one(self.gl.glGenFramebuffers(1))
        self.gl.glBindFramebuffer(self.gl.GL_FRAMEBUFFER, fbo)
        self.gl.glFramebufferTexture2D(self.gl.GL_FRAMEBUFFER, self.gl.GL_COLOR_ATTACHMENT0, self.gl.GL_TEXTURE_2D, color, 0)
        self.gl.glFramebufferRenderbuffer(self.gl.GL_FRAMEBUFFER, self.gl.GL_DEPTH_STENCIL_ATTACHMENT, self.gl.GL_RENDERBUFFER, ds)
        self.gl.glViewport(0, 0, w, h)
        return fbo

    def _make_path(self):
        p = one(self.nv.glGenPathsNV(1))
        self.nv.glPathCommandsNV(
            p, 4, self.commands(), 6, self.gl.GL_FLOAT, COORDS
        )
        return p

    # --- path object creation / parameters / queries ---------------------
    def test_path_core(self):
        self.require_extension('GL_NV_path_rendering')
        p = self._make_path()
        self.assertTrue(self.nv.glIsPathNV(p))

        svg = one(self.nv.glGenPathsNV(1))
        s = b'M0,0 L6,0 L3,6 Z'
        self.nv.glPathStringNV(svg, self.nv.GL_PATH_FORMAT_SVG_NV, len(s), s)

        # editing
        self.nv.glPathSubCommandsNV(p, 0, 0, 1, np.array([self.nv.GL_MOVE_TO_NV], 'u1'), 2, self.gl.GL_FLOAT,
                            np.array([0.0, 0.0], 'f'))
        self.nv.glPathSubCoordsNV(p, 0, 2, self.gl.GL_FLOAT, np.array([0.5, 0.5], 'f'))

        # parameters
        self.nv.glPathParameterfNV(p, self.nv.GL_PATH_STROKE_WIDTH_NV, 1.5)
        self.nv.glPathParameteriNV(p, self.nv.GL_PATH_JOIN_STYLE_NV, self.nv.GL_ROUND_NV)
        self.nv.glPathParameterfvNV(p, self.nv.GL_PATH_STROKE_WIDTH_NV, np.array([1.5], 'f'))
        self.nv.glPathParameterivNV(p, self.nv.GL_PATH_JOIN_STYLE_NV, np.array([self.nv.GL_ROUND_NV], 'i'))
        self.nv.glPathDashArrayNV(p, 2, np.array([2.0, 1.0], 'f'))

        # derive new paths from existing ones (weighting needs >1 compatible path)
        copy = one(self.nv.glGenPathsNV(1))
        self.nv.glCopyPathNV(copy, p)
        weighted = one(self.nv.glGenPathsNV(1))
        self.nv.glWeightPathsNV(weighted, 2, np.array([p, copy], 'u4'), np.array([0.5, 0.5], 'f'))
        interp = one(self.nv.glGenPathsNV(1))
        self.nv.glInterpolatePathsNV(interp, p, copy, 0.5)
        self.nv.glTransformPathNV(copy, p, self.nv.GL_TRANSLATE_X_NV, np.array([1.0], 'f'))

        # queries
        self.nv.glGetPathParameterfvNV(p, self.nv.GL_PATH_STROKE_WIDTH_NV, np.zeros(1, 'f'))
        self.nv.glGetPathParameterivNV(p, self.nv.GL_PATH_JOIN_STYLE_NV, np.zeros(1, 'i'))
        self.nv.glGetPathCommandsNV(p, np.zeros(8, 'u1'))
        self.nv.glGetPathCoordsNV(p, np.zeros(16, 'f'))
        self.nv.glGetPathDashArrayNV(p, np.zeros(2, 'f'))
        self.assertGreaterEqual(float(self.nv.glGetPathLengthNV(p, 0, 4)), 0.0)
        self.nv.glIsPointInFillPathNV(p, 0xFF, 1.0, 1.0)
        self.nv.glIsPointInStrokePathNV(p, 1.0, 1.0)

        self.nv.glDeletePathsNV(svg, 1)
        self.nv.glDeletePathsNV(p, 1)
        self.check_error('nv path rendering core')

    # --- the path matrix stack -------------------------------------------
    def test_path_matrices(self):
        self.require_extension('GL_NV_path_rendering')
        m = self.nv.GL_PATH_MODELVIEW_NV
        ident = ravel(np.eye(4, dtype='f'))
        identd = ravel(np.eye(4, dtype='d'))
        self.nv.glMatrixLoadIdentityEXT(self.nv.GL_PATH_PROJECTION_NV)
        self.nv.glMatrixOrthoEXT(self.nv.GL_PATH_PROJECTION_NV, 0, 16, 0, 16, -1, 1)
        self.nv.glMatrixFrustumEXT(self.nv.GL_PATH_PROJECTION_NV, -1, 1, -1, 1, 1, 10)
        self.nv.glMatrixLoadIdentityEXT(m)
        self.nv.glMatrixLoadfEXT(m, ident)
        self.nv.glMatrixLoaddEXT(m, identd)
        self.nv.glMatrixLoadTransposefEXT(m, ident)
        self.nv.glMatrixLoadTransposedEXT(m, identd)
        self.nv.glMatrixMultfEXT(m, ident)
        self.nv.glMatrixMultdEXT(m, identd)
        self.nv.glMatrixMultTransposefEXT(m, ident)
        self.nv.glMatrixMultTransposedEXT(m, identd)
        self.nv.glMatrixTranslatefEXT(m, 1, 2, 0)
        self.nv.glMatrixTranslatedEXT(m, 1, 2, 0)
        self.nv.glMatrixScalefEXT(m, 2, 2, 1)
        self.nv.glMatrixScaledEXT(m, 2, 2, 1)
        self.nv.glMatrixRotatefEXT(m, 90, 0, 0, 1)
        self.nv.glMatrixRotatedEXT(m, 90, 0, 0, 1)
        self.nv.glMatrixPushEXT(m)
        self.nv.glMatrixPopEXT(m)
        self.nv.glMatrixLoad3x2fNV(m, np.zeros(6, 'f'))
        self.nv.glMatrixLoad3x3fNV(m, np.zeros(9, 'f'))
        self.nv.glMatrixLoadTranspose3x3fNV(m, np.zeros(9, 'f'))
        self.nv.glMatrixMult3x2fNV(m, np.zeros(6, 'f'))
        self.nv.glMatrixMult3x3fNV(m, np.zeros(9, 'f'))
        self.nv.glMatrixMultTranspose3x3fNV(m, np.zeros(9, 'f'))
        self.nv.glMatrixLoadIdentityEXT(m)
        self.check_error('nv path rendering matrices')

    # --- stencil + cover -------------------------------------------------
    def test_path_stencil_cover(self):
        self.require_extension('GL_NV_path_rendering')
        self._stencil_fbo()
        self.nv.glMatrixLoadIdentityEXT(self.nv.GL_PATH_PROJECTION_NV)
        self.nv.glMatrixOrthoEXT(self.nv.GL_PATH_PROJECTION_NV, 0, 16, 0, 16, -1, 1)
        self.nv.glMatrixLoadIdentityEXT(self.nv.GL_PATH_MODELVIEW_NV)
        p = self._make_path()
        paths = np.array([p], 'u4')

        self.nv.glPathStencilFuncNV(self.gl.GL_ALWAYS, 0, 0xFF)
        self.nv.glPathStencilDepthOffsetNV(0.0, 0.0)
        self.nv.glPathCoverDepthFuncNV(self.gl.GL_ALWAYS)

        self.nv.glStencilFillPathNV(p, self.nv.GL_COUNT_UP_NV, 0xFF)
        self.nv.glCoverFillPathNV(p, self.nv.GL_BOUNDING_BOX_NV)
        self.nv.glStencilStrokePathNV(p, 1, 0xFF)
        self.nv.glCoverStrokePathNV(p, self.nv.GL_CONVEX_HULL_NV)
        self.nv.glStencilThenCoverFillPathNV(p, self.nv.GL_COUNT_UP_NV, 0xFF, self.nv.GL_BOUNDING_BOX_NV)
        self.nv.glStencilThenCoverStrokePathNV(p, 1, 0xFF, self.nv.GL_CONVEX_HULL_NV)

        self.nv.glStencilFillPathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, self.nv.GL_COUNT_UP_NV, 0xFF, self.gl.GL_NONE, None)
        self.nv.glCoverFillPathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, self.nv.GL_BOUNDING_BOX_NV, self.gl.GL_NONE, None)
        self.nv.glStencilStrokePathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, 1, 0xFF, self.gl.GL_NONE, None)
        self.nv.glCoverStrokePathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, self.nv.GL_CONVEX_HULL_NV, self.gl.GL_NONE, None)
        self.nv.glStencilThenCoverFillPathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, self.nv.GL_COUNT_UP_NV, 0xFF, self.nv.GL_BOUNDING_BOX_NV, self.gl.GL_NONE, None)
        self.nv.glStencilThenCoverStrokePathInstancedNV(1, self.gl.GL_UNSIGNED_INT, paths, 0, 1, 0xFF, self.nv.GL_CONVEX_HULL_NV, self.gl.GL_NONE, None)
        self.gl.glBindFramebuffer(self.gl.GL_FRAMEBUFFER, 0)
        self.check_error('nv path rendering stencil/cover')

    # --- metrics / spacing / point-along ---------------------------------
    def test_path_metrics(self):
        self.require_extension('GL_NV_path_rendering')
        p = self._make_path()
        paths = np.array([p, p], 'u4')
        mask = self.nv.GL_GLYPH_WIDTH_BIT_NV | self.nv.GL_GLYPH_HEIGHT_BIT_NV
        self.nv.glGetPathMetricsNV(mask, 2, self.gl.GL_UNSIGNED_INT, paths, 0, 0, np.zeros(4, 'f'))
        self.nv.glGetPathMetricRangeNV(mask, p, 1, 0, np.zeros(2, 'f'))
        self.nv.glGetPathSpacingNV(self.nv.GL_ACCUM_ADJACENT_PAIRS_NV, 2, self.gl.GL_UNSIGNED_INT, paths, 0,
                           1.0, 1.0, self.nv.GL_TRANSLATE_X_NV, np.zeros(2, 'f'))
        self.nv.glPointAlongPathNV(p, 0, 4, 1.0, np.zeros(1, 'f'), np.zeros(1, 'f'),
                           np.zeros(1, 'f'), np.zeros(1, 'f'))
        self.check_error('nv path rendering metrics')

    # --- colour / tex / fog gen + program fragment input -----------------
    def test_path_gen(self):
        self.require_extension('GL_NV_path_rendering')
        coeffs = np.zeros((2, 3), 'f')
        self.nv.glPathColorGenNV(self.nv.GL_PRIMARY_COLOR, self.nv.GL_PATH_OBJECT_BOUNDING_BOX_NV, self.gl.GL_RGBA,
                         np.zeros((4, 3), 'f'))
        self.nv.glPathTexGenNV(self.gl.GL_TEXTURE0, self.nv.GL_PATH_OBJECT_BOUNDING_BOX_NV, 2, coeffs)
        # self.nv.glPathFogGenNV is part of the deprecated fixed-function fog path and is
        # rejected (self.gl.GL_INVALID_ENUM for every mode) by current NVIDIA drivers.
        self.nv.glGetPathColorGenfvNV(self.nv.GL_PRIMARY_COLOR, self.nv.GL_PATH_GEN_MODE_NV, np.zeros(4, 'f'))
        self.nv.glGetPathColorGenivNV(self.nv.GL_PRIMARY_COLOR, self.nv.GL_PATH_GEN_MODE_NV, np.zeros(4, 'i'))
        self.nv.glGetPathTexGenfvNV(self.gl.GL_TEXTURE0, self.nv.GL_PATH_GEN_MODE_NV, np.zeros(4, 'f'))
        self.nv.glGetPathTexGenivNV(self.gl.GL_TEXTURE0, self.nv.GL_PATH_GEN_MODE_NV, np.zeros(4, 'i'))

        # build without the strict validate pass -- a path fragment input is fed
        # by the path's gen state, not by a vertex stage, so self.gl.glValidateProgram
        # would (correctly) flag it in an ordinary pipeline.
        from OpenGL.GL import shaders
        vs = shaders.compileShader(
            '#version 450 compatibility\n'
            'layout(location=0) out vec2 tc;\n'
            'void main(){ tc = vec2(0.0); gl_Position = vec4(0.0); }',
            self.gl.GL_VERTEX_SHADER,
        )
        fs = shaders.compileShader(
            '#version 450 compatibility\n'
            'layout(location=0) in vec2 tc; out vec4 c;\n'
            'void main(){ c = vec4(tc, 0.0, 1.0); }',
            self.gl.GL_FRAGMENT_SHADER,
        )
        program = self.gl.glCreateProgram()
        self.gl.glAttachShader(program, vs)
        self.gl.glAttachShader(program, fs)
        self.gl.glLinkProgram(program)
        if not self.gl.glGetProgramiv(program, self.gl.GL_LINK_STATUS):
            self.skipTest('path fragment-input program did not link')
        idx = one(self.gl.glGetProgramResourceIndex(program, self.nv.GL_FRAGMENT_INPUT_NV, b'tc'))
        # explicit layout(location=0) on the fragment input
        self.nv.glProgramPathFragmentInputGenNV(program, 0, self.nv.GL_OBJECT_LINEAR_NV, 2,
                                        np.zeros((2, 3), 'f'))
        self.nv.glGetProgramResourcefvNV(program, self.nv.GL_FRAGMENT_INPUT_NV, idx, 1,
                                 np.array([self.nv.GL_PATH_GEN_COEFF_NV], 'u4'), 4,
                                 np.zeros(1, 'i'), np.zeros(4, 'f'))
        self.check_error('nv path rendering gen')

    # --- glyphs (need a font) --------------------------------------------
    def test_path_glyphs(self):
        self.require_extension('GL_NV_path_rendering')
        from OpenGL import error

        base = int(self.nv.glGenPathsNV(256))
        try:
            self.nv.glPathGlyphRangeNV(base, self.nv.GL_STANDARD_FONT_NAME_NV, b'Sans', 0, 0, 256,
                               self.nv.GL_SKIP_MISSING_GLYPH_NV, 0, 64.0)
        except error.GLError:
            self.skipTest('no usable font for NV_path_rendering glyphs on this host')
        if self.gl.glGetError() != self.gl.GL_NO_ERROR:
            self.skipTest('no usable font for NV_path_rendering glyphs on this host')

        self.nv.glPathGlyphsNV(base, self.nv.GL_STANDARD_FONT_NAME_NV, b'Sans', 0, 2, self.gl.GL_UNSIGNED_BYTE,
                       b'Hi', self.nv.GL_SKIP_MISSING_GLYPH_NV, 0, 64.0)
        # self.gl.glPathGlyphIndex{Range,Array}NV / self.nv.glPathMemoryGlyphIndexArrayNV map glyph
        # *indices*, which the built-in standard fonts do not expose -- they need a
        # real font file/blob unavailable on a headless host.
        self.check_error('nv path rendering glyphs')
