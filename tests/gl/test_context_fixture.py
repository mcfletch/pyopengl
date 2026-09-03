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

from gltestcase import GLTestCase

from OpenGL.GL import glCreateProgram, glDeleteProgram, glGenBuffers, glDeleteBuffers


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
        self.defer_cleanup(lambda: glDeleteBuffers(1, [buffers]))
        assert buffers is not None
