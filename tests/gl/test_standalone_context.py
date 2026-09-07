#! /usr/bin/env python3
"""A context outside a TestCase, on whichever backend this machine offers.

Several cases here are not rendering cases and cannot be one: they need two
contexts at once, or a context on a worker thread, or a fresh interpreter to
settle a question that is settled once per process.  Each used to open a GLFW
window of its own, which made them absent -- skipped, quietly -- on a machine
whose contexts come from somewhere else: an EGL device in a container, CGL on
a macOS runner with no window server.

:class:`glcontext.Context` is ``pick_backend()`` for those cases, so they run
wherever the rendering suites run.
"""

import unittest

import pytest

from glcontext import Context


class TestOneContext(unittest.TestCase):
    def test_it_is_current_once_made(self):
        from OpenGL import platform

        with Context() as context:
            assert context.handle
            assert context.handle == platform.PLATFORM.GetCurrentContext()

    def test_it_draws(self):
        """A context nothing can be called through is not a context."""
        from OpenGL.GL import GL_VERSION, glGetString

        with Context():
            assert glGetString(GL_VERSION)

    def test_what_it_asks_for_is_what_it_asks_the_backend_for(self):
        with Context(gl_version=(3, 3), profile='core') as context:
            assert context.gl_version == (3, 3)
            assert context.profile == 'core'

    def test_a_version_the_machine_will_not_give_is_a_skip(self):
        """Not a failure: a machine that cannot serve the request has not
        broken anything, and the case that wanted it has nothing to say."""
        with pytest.raises(unittest.SkipTest):
            Context(gl_version=(9, 9))


class TestSeveralAtOnce(unittest.TestCase):
    """What the multi-context cases need: contexts that do not disturb
    each other, and a way to say which one is being talked to."""

    def test_each_is_its_own(self):
        with Context() as first, Context() as second:
            assert first.handle
            assert second.handle
            assert first.handle != second.handle

    def test_making_one_current_makes_it_the_current_one(self):
        from OpenGL import platform

        with Context() as first, Context() as second:
            first.make_current()
            assert platform.PLATFORM.GetCurrentContext() == first.handle
            second.make_current()
            assert platform.PLATFORM.GetCurrentContext() == second.handle

    def test_releasing_one_leaves_the_other(self):
        with Context() as first:
            second = Context()
            second.release()
            first.make_current()
            from OpenGL.GL import GL_VERSION, glGetString

            assert glGetString(GL_VERSION)


class TestGivingItBack(unittest.TestCase):
    def test_release_is_idempotent(self):
        """A caller that released explicitly still leaves the block."""
        context = Context()
        context.release()
        context.release()


if __name__ == '__main__':
    unittest.main()
