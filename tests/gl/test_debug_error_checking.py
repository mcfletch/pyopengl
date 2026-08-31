#! /usr/bin/env python3
"""Error checking through GL_KHR_debug rather than a glGetError per call.

A per-call ``glGetError`` is a driver round trip, and it is the whole cost of
error checking.  Where the context offers ``GL_KHR_debug``, the driver reports
an error through a callback instead, and checking becomes a read of a flag the
callback set.  What the caller sees does not change: the same exception, from
the same call.
"""

import time
import unittest

import pytest

from gltestcase import GLTestCase
from OpenGL import error
from OpenGL.GL import *  # noqa: F401,F403

import OpenGL._dispatch as dispatch


@pytest.mark.skipif(
    not dispatch.AVAILABLE, reason='the C dispatch extension is not built'
)
class TestDebugErrorChecking(GLTestCase):
    profile = 'core'
    gl_version = (4, 3)

    def setUp(self):
        super().setUp()
        if not dispatch.ACTIVE:
            self.skipTest('PYOPENGL_DISPATCH=c selects the implementation under test')
        if not dispatch.debug_output_available():
            self.skipTest('this context has no GL_KHR_debug')

    def tearDown(self):
        dispatch.use_debug_output(False)
        super().tearDown()

    def test_an_invalid_call_raises(self):
        dispatch.use_debug_output(True)
        with pytest.raises(error.GLError):
            glEnable(0xDEAD)

    def test_the_error_names_the_call_that_caused_it(self):
        dispatch.use_debug_output(True)
        try:
            glEnable(0xDEAD)
        except error.GLError as raised:
            assert 'glEnable' in str(raised.baseOperation or '')
        else:
            self.fail('no error raised')

    def test_a_valid_call_does_not_raise(self):
        dispatch.use_debug_output(True)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_DEPTH_TEST)

    def test_one_error_does_not_leak_into_the_next_call(self):
        dispatch.use_debug_output(True)
        with pytest.raises(error.GLError):
            glEnable(0xDEAD)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_DEPTH_TEST)

    def test_it_costs_less_than_a_glGetError_per_call(self):
        """The point of the exercise: checking stops being a round trip."""

        def measure(count=20000):
            glBindTexture(GL_TEXTURE_2D, 0)
            best = None
            for _ in range(3):
                start = time.perf_counter()
                for _ in range(count):
                    glBindTexture(GL_TEXTURE_2D, 0)
                elapsed = time.perf_counter() - start
                best = elapsed if best is None else min(best, elapsed)
            return best / count * 1e9

        dispatch.use_debug_output(False)
        dispatch.set_error_checking(True)
        with_get_error = measure()

        dispatch.use_debug_output(True)
        with_debug = measure()

        assert with_debug < with_get_error, (with_debug, with_get_error)


if __name__ == '__main__':
    unittest.main()
