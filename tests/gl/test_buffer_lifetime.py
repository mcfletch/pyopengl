#! /usr/bin/env python3
"""Buffers acquired for a call are released, on every path out of it.

``PyObject_GetBuffer`` raises the exporter's export count and takes a
reference to it, and failing to release the buffer leaks both.  The error
paths are what make this worth asserting: a call that
acquires one array and then fails converting a second must still release the
first, and functions taking two arrays are ordinary.
"""

import contextlib
import gc
import sys
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


@contextlib.contextmanager
def no_buffer_left_exported(*arrays):
    """Assert each array leaves the block with no buffer of it still held.

    ``PyObject_GetBuffer`` takes a reference to the exporter and
    ``PyBuffer_Release`` hands it back, so a buffer acquired and not released
    shows as a reference the array did not have going in.  That reference is
    what there is to see: a numpy array with a live export used to refuse to
    have its shape set, which is what this asked before, and from numpy 2.5 it
    no longer does -- so the question had stopped being asked at all.

    Both counts are read by the same expression, because ``getrefcount`` sees
    whatever the reading itself is holding -- a loop that unpacks the arrays
    differently from the comprehension that counted them reports the machinery
    rather than the call.
    """
    before = [sys.getrefcount(array) for array in arrays]
    yield
    gc.collect()
    after = [sys.getrefcount(array) for array in arrays]
    assert after == before, (
        'references taken during the call and not given back: %r -- a buffer '
        'acquired and not released' % ([a - b for a, b in zip(after, before)],)
    )


class TestBufferLifetime(GLTestCase):
    profile = 'compat'

    def test_a_successful_call_releases_its_buffer(self):
        values = np.zeros(3, 'd')
        with no_buffer_left_exported(values):
            glVertex3dv(values)

    def test_a_failing_size_check_releases_its_buffer(self):
        values = np.zeros(4, 'd')
        with no_buffer_left_exported(values):
            with pytest.raises((ValueError, TypeError)):
                glVertex3dv(values)

    def test_two_arrays_are_both_released(self):
        """``glMultiDrawArrays(mode, first, count, drawcount)`` takes two.

        With a draw count of zero it draws nothing, which is the point: what
        is under test is the cleanup frame, not the drawing.  A legacy
        client-side draw would exercise the same frame but faults inside the
        driver outside a compatibility profile, under either implementation.
        """
        first = np.zeros(2, 'i')
        count = np.zeros(2, 'i')
        with no_buffer_left_exported(first, count):
            glMultiDrawArrays(GL_TRIANGLES, first, count, 0)

    def test_a_failure_after_a_successful_acquisition_releases_it(self):
        """The first array is acquired; the second cannot be converted.

        This is the case the cleanup frame exists for: without it the first
        buffer stays exported for the life of the array.
        """
        first = np.zeros(2, 'i')
        with no_buffer_left_exported(first):
            with pytest.raises(Exception):
                glMultiDrawArrays(GL_TRIANGLES, first, object(), 0)

    def test_the_argument_is_not_kept_alive_after_the_call(self):
        values = np.zeros(3, 'd')
        before = sys.getrefcount(values)
        for _ in range(100):
            glVertex3dv(values)
        gc.collect()
        assert sys.getrefcount(values) == before

    def test_an_output_array_survives_being_returned(self):
        """What comes back is a live array, not a view over freed memory."""
        textures = glGenTextures(4)
        gc.collect()
        assert len(list(textures)) == 4
        assert all(int(name) > 0 for name in textures)

    def test_a_passed_in_output_is_not_left_exported(self):
        into = np.zeros(4, 'I')
        with no_buffer_left_exported(into):
            # Not bound to a name: what comes back *is* the array, so holding
            # it would be a reference the block is entitled to see.
            assert glGenTextures(4, into) is into


if __name__ == '__main__':
    unittest.main()
