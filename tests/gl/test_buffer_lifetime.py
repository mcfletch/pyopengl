#! /usr/bin/env python3
"""Buffers acquired for a call are released, on every path out of it.

``PyObject_GetBuffer`` raises the exporter's export count, and failing to
release it blocks a numpy resize, blocks ``memoryview.release()`` and leaks a
reference.  The error paths are what make this worth asserting: a call that
acquires one array and then fails converting a second must still release the
first, and functions taking two arrays are ordinary.
"""

import gc
import sys
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


def exports_are_clear(array):
    """Whether every buffer taken from this array has been released.

    A numpy array with a live export refuses to have its shape set, and says
    so; that is the cheapest way to ask from Python.
    """
    try:
        array.shape = array.shape
    except (ValueError, AttributeError):
        return False
    return True


class TestBufferLifetime(GLTestCase):
    profile = 'compat'

    def test_a_successful_call_releases_its_buffer(self):
        values = np.zeros(3, 'd')
        glVertex3dv(values)
        assert exports_are_clear(values)

    def test_a_failing_size_check_releases_its_buffer(self):
        values = np.zeros(4, 'd')
        with pytest.raises((ValueError, TypeError)):
            glVertex3dv(values)
        assert exports_are_clear(values)

    def test_two_arrays_are_both_released(self):
        """``glDrawElements`` takes an index array beside its scalars.

        A deprecated entry point would be the obvious choice here, but
        ``bool(glFoo)`` says the driver exports the symbol, not that the
        current profile will accept a call to it -- and a compatibility-only
        entry point called under a core profile faults inside the driver,
        under either implementation.
        """
        indices = np.zeros(3, 'I')
        buffer = np.zeros(9, 'f')
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            glVertexPointer(3, GL_FLOAT, 0, buffer)
            glDrawElements(GL_TRIANGLES, 3, GL_UNSIGNED_INT, indices)
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)
        assert exports_are_clear(indices)
        assert exports_are_clear(buffer)

    def test_a_failure_after_a_successful_acquisition_releases_it(self):
        """The first array is acquired; the second cannot be converted.

        This is the case the cleanup frame exists for: without it the first
        buffer stays exported for the life of the array.
        """
        buffer = np.zeros(9, 'f')
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            glVertexPointer(3, GL_FLOAT, 0, buffer)
            with pytest.raises(Exception):
                glDrawElements(GL_TRIANGLES, 3, GL_UNSIGNED_INT, object())
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)
        assert exports_are_clear(buffer)

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
        result = glGenTextures(4, into)
        assert result is into
        assert exports_are_clear(into)


if __name__ == '__main__':
    unittest.main()
