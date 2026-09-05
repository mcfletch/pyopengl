#! /usr/bin/env python3
"""Desktop-OpenGL (and GLU) API bases for the shared context test framework.

These bind :class:`glcontext.ContextTestCase` to the desktop ``OpenGL.GL`` (and,
for GLU, ``OpenGL.GLU``) entry points.  Window/context creation still comes from
a backend mixin chosen by :func:`glcontext.pick_backend`; these classes only
supply ``self.gl`` / ``self.gl3`` and the desktop-/GLU-specific helpers.
"""

from __future__ import print_function

import contextlib

from OpenGL import GL as _gl
from OpenGL import GLU as _glu

from glcontext import ContextTestCase


class DesktopGLTestCaseBase(ContextTestCase):
    """API base for desktop OpenGL tests (``OpenGL.GL``)."""

    api = 'gl'
    profile = 'compatibility'
    gl_version = (2, 1)
    stencil_size = 8

    #: Whether this case calls into GLU.  It is a separate library and a
    #: deprecated one -- an image carrying Mesa's GL often has no libGLU at
    #: all -- so a case that needs it says so and is skipped where it is
    #: absent, rather than raising NullFunctionError from its own setUp and
    #: reading as a broken test instead of an absent dependency.
    needs_glu = False

    #: desktop GL exports both the core entry points and the indexed query.
    gl = _gl
    gl3 = _gl

    def setUp(self):
        if self.needs_glu:
            from OpenGL import platform

            if getattr(platform.PLATFORM, 'GLU', None) is None:
                self.skipTest('this case needs GLU and the library is not here')
        super().setUp()

    def _setup_default_objects(self):
        # The core profile requires a bound VAO for any vertex operation.
        self._vao = None
        if self.profile.lower() == 'core' and self.gl_version >= (3, 0):
            self._vao = _gl.glGenVertexArrays(1)
            _gl.glBindVertexArray(self._vao)

    def assert_profile(self, expected):
        """Portably assert the context profile ('core' or 'compatibility').

        Drivers disagree on whether GL_VERSION names the profile -- Mesa embeds
        ``(Core Profile)`` / ``(Compatibility Profile)``; NVIDIA does not -- so
        query GL_CONTEXT_PROFILE_MASK, which is defined for GL >= 3.2.  Below 3.2
        there is no core/compatibility split (immediate mode is always present),
        so only a 'compatibility' expectation is meaningful there.
        """
        expected = expected.lower()
        if self.version() >= (3, 2):
            mask = self.getInteger(_gl.GL_CONTEXT_PROFILE_MASK)
            bit = (
                _gl.GL_CONTEXT_CORE_PROFILE_BIT
                if expected == 'core'
                else _gl.GL_CONTEXT_COMPATIBILITY_PROFILE_BIT
            )
            self.assertTrue(
                mask & bit,
                'expected a %s-profile context (GL_CONTEXT_PROFILE_MASK=0x%x)'
                % (expected, mask),
            )
        else:
            self.assertEqual(
                expected, 'compatibility',
                'pre-3.2 contexts are compatibility/immediate-mode only',
            )

    # --- shader helper ----------------------------------------------------
    def compile_program(self, vertex_src, fragment_src, extra_stages=()):
        from OpenGL.GL import shaders, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER

        stages = [
            shaders.compileShader(vertex_src, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_src, GL_FRAGMENT_SHADER),
        ]
        for stage_enum, source in extra_stages:
            stages.append(shaders.compileShader(source, stage_enum))
        program = shaders.compileProgram(*stages)
        self.check_error('compile_program')
        return program

    # --- immediate mode ---------------------------------------------------
    @contextlib.contextmanager
    def begin(self, mode):
        """A ``glBegin``/``glEnd`` block that is closed however the body ends.

        ``glGetError`` is illegal between the two, so PyOpenGL suspends error
        checking for the block and ``glEnd`` turns it back on.  A body that
        raises -- an entry point the driver does not export, a bad vertex --
        leaves the block open, and with it the checking that every later case
        in the process depends on.
        """
        self.gl.glBegin(mode)
        try:
            yield
        finally:
            self.gl.glEnd()


class GLUTestCaseBase(DesktopGLTestCaseBase):
    """API base for GLU tests: a compatibility GL context plus GLU helpers.

    GLU rides on the fixed-function pipeline (gluProject reads
    ``GL_MODELVIEW_MATRIX`` / ``GL_PROJECTION_MATRIX``; quadrics / tess / NURBS
    emit immediate-mode geometry), so the context is always compatibility.
    """

    #: GLU needs the fixed-function pipeline, so always a compatibility context.
    profile = 'compatibility'
    #: 2.1 is the highest pure-compat target.
    gl_version = (2, 1)
    needs_glu = True

    # --- GLU object factories (registered for teardown cleanup) ----------
    def quadric(self):
        """Return a fresh GLUquadric, deleted automatically at teardown."""
        q = _glu.gluNewQuadric()
        self.defer_cleanup(lambda: _glu.gluDeleteQuadric(q))
        return q

    def tessellator(self):
        """Return a fresh GLUtesselator, deleted automatically at teardown."""
        tess = _glu.gluNewTess()
        self.defer_cleanup(lambda: _glu.gluDeleteTess(tess))
        return tess

    def nurbs(self):
        """Return a fresh GLUnurbs renderer, deleted automatically at teardown."""
        nurb = _glu.gluNewNurbsRenderer()
        self.defer_cleanup(lambda: _glu.gluDeleteNurbsRenderer(nurb))
        return nurb

    # --- matrix helpers ---------------------------------------------------
    def set_projection(self, fovy=40.0, near=0.1, far=100.0):
        """Install a gluPerspective projection and an identity modelview.

        Leaves the matrix mode at GL_MODELVIEW (the usual drawing state) so the
        projection / unprojection helpers have well-defined matrices to read.
        """
        aspect = float(self.width) / float(self.height or 1)
        _gl.glMatrixMode(_gl.GL_PROJECTION)
        _gl.glLoadIdentity()
        _glu.gluPerspective(fovy, aspect, near, far)
        _gl.glMatrixMode(_gl.GL_MODELVIEW)
        _gl.glLoadIdentity()
        self.check_error('set_projection')

    def gluVersion(self):
        """Return the GLU library version as a (major, minor) int tuple."""
        raw = _glu.gluGetString(_glu.GLU_VERSION)
        if isinstance(raw, bytes):
            raw = raw.decode('ascii', 'replace')
        parts = (raw or '0.0').split('.')
        return tuple(int(p) for p in parts[:2])
