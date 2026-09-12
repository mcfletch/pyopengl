#! /usr/bin/env python3
"""What one entry point call costs, for the calls a frame makes thousands of.

A renderer's inner loop is state changes: bind a texture, set the active
texture unit, bind a buffer, set a uniform. None of them draws anything, and a
frame makes thousands, so the per-call overhead PyOpenGL adds is multiplied by
a number the profile of any real program is dominated by.

The regression these guard against is not a slow driver but a slow *wrapper*:
a call that acquires the context, rebuilds a converter, or asks the platform
something on every invocation rather than once. #95 reports exactly that shape
-- ``glActiveTexture`` becoming slow enough between two releases that the
program did not get as far as rendering -- against a Qt program whose context
PyOpenGL was mis-identifying, which is the platform-selection defect fixed
separately.

Marked ``performance``: these measure the machine as much as the library, so
``tox`` deselects them and a bare ``pytest`` on an idle machine runs them.
The bound is loose on purpose. It is not a benchmark; it is the difference
between "a wrapper call" and "a wrapper call that does something expensive it
should have done once", which is two orders of magnitude and needs no
precision to see.

https://github.com/mcfletch/pyopengl/issues/95
"""

import time
import unittest

import pytest

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

#: Microseconds a state-setting call may take on average.  A ctypes call with
#: no conversion is well under one; the C dispatch layer is under a tenth.
#: Ten is "something is being rebuilt or re-queried per call".
SLOWEST_REASONABLE_US = 10.0

#: Enough calls that the timer's own resolution does not matter, and few
#: enough to stay fast on the software renderer.
CALLS = 5000


@pytest.mark.performance
class TestAStateChangeIsCheap(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def cost_of(self, call, *args):
        """Microseconds per call, after a warm-up that resolves the pointer."""
        call(*args)
        glFinish()
        started = time.perf_counter()
        for _ in range(CALLS):
            call(*args)
        glFinish()
        return (time.perf_counter() - started) / CALLS * 1e6

    def assert_cheap(self, name, call, *args):
        per_call = self.cost_of(call, *args)
        self.assertLess(
            per_call, SLOWEST_REASONABLE_US,
            '%s costs %.2f us per call, which is not a wrapper call but a '
            'wrapper call doing something per-call it should do once'
            % (name, per_call))

    def test_gl_active_texture(self):
        self.assert_cheap('glActiveTexture', glActiveTexture, GL_TEXTURE0)

    def test_gl_bind_texture(self):
        self.assert_cheap('glBindTexture', glBindTexture, GL_TEXTURE_2D, 0)

    def test_gl_bind_buffer(self):
        self.assert_cheap('glBindBuffer', glBindBuffer, GL_ARRAY_BUFFER, 0)

    def test_gl_enable(self):
        self.assert_cheap('glEnable', glEnable, GL_DEPTH_TEST)


if __name__ == '__main__':
    unittest.main()
