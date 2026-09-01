#! /usr/bin/env python3
"""What the entry points accept where an array is wanted.

The rule the C dispatch layer is held to is that its fast path may accelerate
but never reject: an argument the ctypes layer would have converted is
converted, and an argument it would have refused is refused with the same kind
of exception.  These cases run under whichever implementation is selected, so
the same file asserts the contract for both.
"""

import ctypes
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestArrayAcceptance(GLTestCase):
    profile = 'compat'

    def test_matching_dtype_is_accepted(self):
        glVertex3dv(np.zeros(3, 'd'))

    def test_mismatched_dtype_is_converted(self):
        """Passing float32 where float64 is wanted is ordinary client code."""
        glVertex3dv(np.zeros(3, 'f'))
        glVertex3dv(np.zeros(3, 'i'))

    def test_sequences_are_converted(self):
        glVertex3dv([1.0, 2.0, 3.0])
        glVertex3dv((1.0, 2.0, 3.0))

    def test_ctypes_arrays_are_accepted(self):
        glVertex3dv((ctypes.c_double * 3)(1.0, 2.0, 3.0))

    def test_memoryview_is_accepted(self):
        glVertex3dv(memoryview(np.zeros(3, 'd')))

    def test_too_short_is_refused_rather_than_read_past(self):
        """A wrongly sized array must raise, not hand the driver a short read.

        An empty sequence is the case that matters most: it converts to a
        zero-length array whose data pointer is null, and a size check that
        skipped null pointers would let the driver read from address zero.
        """
        for bad in ([], (), np.zeros(2, 'd'), np.zeros(0, 'd')):
            with pytest.raises((ValueError, TypeError)):
                glVertex3dv(bad)

    def test_too_long_is_refused(self):
        with pytest.raises((ValueError, TypeError)):
            glVertex3dv(np.zeros(4, 'd'))

    def test_none_is_a_null_pointer_where_one_is_meaningful(self):
        """An unbound client array is a null pointer, not an error."""
        glVertexPointer(3, GL_FLOAT, 0, None)


if __name__ == '__main__':
    unittest.main()
