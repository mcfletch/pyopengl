#! /usr/bin/env python3
"""OpenGL-ES API base for the shared context test framework.

Binds :class:`glcontext.ContextTestCase` to the ``OpenGL.GLES2`` / ``GLES3``
entry points.  Window/context creation comes from a backend mixin chosen by
:func:`glcontext.pick_backend`; this class supplies ``self.gl`` / ``self.gl3``
and the ES-specific shader helpers.
"""

from __future__ import print_function

# OpenGL-ES is reached through the EGL platform, which PYOPENGL_PLATFORM has to
# name before anything imports OpenGL at all.  tests/conftest.py sets it, since
# that runs before any test module: setting it here would be both too late to
# take effect and early enough to change the platform for every subprocess the
# rest of the run starts.

# The generic GL entry points we use for introspection / readback all live in
# (and are shared by) the GLES2 namespace; individual tests still import the
# specific GLES1/GLES2/GLES3 module that matches their tier.
from OpenGL import GLES2 as _gl
from OpenGL import GLES3 as _gl3

from glcontext import ContextTestCase


class ESTestCaseBase(ContextTestCase):
    """API base for OpenGL-ES rendering tests (``OpenGL.GLES2`` / ``GLES3``)."""

    api = 'gles'
    gl_version = (2, 0)
    stencil_size = 0

    gl = _gl
    gl3 = _gl3

    def setUp(self):
        # OpenGL-ES is not part of every platform: Windows and macOS have no ES
        # library unless something has installed ANGLE beside the application,
        # and the entry points then fall back to the desktop library, which is
        # a different API wearing the same names.
        from OpenGL.platform import PLATFORM

        if PLATFORM.GLES2 is None:
            self.skipTest('this platform has no OpenGL-ES library')
        # ES contexts are only reliably created through EGL; the pygame/SDL
        # backend cannot guarantee a usable ES context on desktop drivers, so
        # skip rather than fail when it is the selected backend.
        if getattr(self, 'backend_name', None) == 'pygame':
            self.skipTest('OpenGL-ES tests require the glfw windowing backend')
        super(ESTestCaseBase, self).setUp()

    # --- shader helpers ---------------------------------------------------
    def compile_program(self, vertex_src, fragment_src, extra_stages=()):
        """Compile + link a program from GLSL source for the current context.

        ``extra_stages`` is a sequence of ``(stage_enum, source)`` pairs for
        additional stages (e.g. a geometry shader).
        """
        from OpenGL.GLES2 import shaders

        stages = [
            shaders.compileShader(vertex_src, _gl.GL_VERTEX_SHADER),
            shaders.compileShader(fragment_src, _gl.GL_FRAGMENT_SHADER),
        ]
        for stage_enum, source in extra_stages:
            stages.append(shaders.compileShader(source, stage_enum))
        program = shaders.compileProgram(*stages)
        self.check_error('compile_program')
        return program

    def compile_compute(self, source):
        """Compile + link a compute-only program (ES3.1+)."""
        from OpenGL.GLES2 import shaders
        from OpenGL.GLES3 import GL_COMPUTE_SHADER

        program = shaders.compileProgram(
            shaders.compileShader(source, GL_COMPUTE_SHADER)
        )
        self.check_error('compile_compute')
        return program
