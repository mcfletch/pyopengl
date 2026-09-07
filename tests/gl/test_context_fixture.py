#! /usr/bin/env python3
"""The context outlives everything a test registers to clean up.

``unittest`` runs ``tearDown()`` and only then ``doCleanups()``, so a fixture
that destroys the context in ``tearDown`` destroys it before any
``addCleanup()`` the test registered has run.  A cleanup that deletes a GL
object then has no context to delete it in.

That is not a quiet no-op on Windows.  An entry point above GL 1.1 is resolved
through ``wglGetProcAddress``, which answers only while a context is current;
with none, the call raises NullFunctionError from inside a cleanup handler,
where a test can neither see it coming nor do anything about it.
"""

from arraycompat import object_names
from gltestcase import GLTestCase

from OpenGL.GL import (
    glCreateProgram,
    glDeleteProgram,
    glGenBuffers,
    glDeleteBuffers,
    glGenFramebuffers,
    glDeleteFramebuffers,
)


class TestCleanupOrdering(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_addcleanup_runs_while_the_context_is_current(self):
        """addCleanup is what a test author reaches for; it has to work."""
        program = glCreateProgram()
        self.addCleanup(glDeleteProgram, program)
        assert program

    def test_defer_cleanup_runs_while_the_context_is_current(self):
        """The fixture's own mechanism, which runs during tearDown."""
        buffers = glGenBuffers(1)
        self.defer_cleanup(lambda: glDeleteBuffers(1, object_names(buffers)))
        assert buffers is not None


class TestPuttingTheFramebufferBack(GLTestCase):
    """A block that borrowed the framebuffer restores what it borrowed from.

    Restoring by binding zero is the tempting shorthand and it is wrong twice
    over: it discards an outer block's framebuffer, and framebuffer zero is the
    drawable's, which a headless CGL context does not have.  Bound there, the
    context has nothing complete to draw into and the next drawing call answers
    ``GL_INVALID_FRAMEBUFFER_OPERATION`` -- against the draw, saying nothing
    about the unbind that caused it.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def setUp(self):
        super().setUp()
        self.require_extension('GL_ARB_framebuffer_object')

    def _framebuffer(self):
        fbo = int(glGenFramebuffers(1))
        self.defer_cleanup(lambda: glDeleteFramebuffers(1, object_names(fbo)))
        return fbo

    def test_a_nested_block_comes_back_to_the_outer_one(self):
        outer, inner = self._framebuffer(), self._framebuffer()
        with self.framebuffer(outer):
            with self.framebuffer(inner):
                assert self.draw_framebuffer() == inner
            assert self.draw_framebuffer() == outer

    def test_and_the_outermost_to_whatever_the_fixture_drew_into(self):
        started_with = self.draw_framebuffer()
        with self.framebuffer(self._framebuffer()):
            pass
        assert self.draw_framebuffer() == started_with

    def test_a_block_that_raises_restores_it_too(self):
        outer = self._framebuffer()
        with self.framebuffer(outer):
            try:
                with self.framebuffer(self._framebuffer()):
                    raise RuntimeError('what the body did')
            except RuntimeError:
                pass
            assert self.draw_framebuffer() == outer
