#! /usr/bin/env python3
"""What the entry points accept where an array is wanted.

The rule the C dispatch layer is held to is that its fast path may accelerate
but never reject: an argument the ctypes layer would have converted is
converted, and an argument it would have refused is refused with the same kind
of exception.  These cases run under whichever implementation is selected, so
the same file asserts the contract for both.
"""

import ctypes
import struct
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
import OpenGL
from OpenGL import acceleratesupport, arrays, _configflags
from OpenGL.GL import *  # noqa: F401,F403

#: ``ARRAY_SIZE_CHECKING`` is what makes a wrongly sized array an exception
#: rather than a short read the driver performs.  A run that has switched it
#: off has asked for the unchecked call, so the cases below are asserting a
#: refusal that is not this configuration's to make.  Read from
#: ``_configflags`` rather than ``OpenGL``: the flag is fixed when the wrappers
#: are built, and that is the module holding the value they were built with.
needs_size_checking = pytest.mark.skipif(
    not _configflags.ARRAY_SIZE_CHECKING,
    reason='ARRAY_SIZE_CHECKING is off, so a wrongly sized array is not refused',
)


class TestArrayAcceptance(GLTestCase):
    profile = 'compat'

    def test_matching_dtype_is_accepted(self):
        glVertex3dv(np.zeros(3, 'd'))

    def test_mismatched_dtype_is_converted(self):
        """Passing float32 where float64 is wanted is ordinary client code.

        numpy's own, since converting between element types is what its handler
        does. ``arraycompat``'s no-numpy shim hands back a plain ctypes array of
        the GL type asked for, and a ``c_float * 3`` where three doubles are
        wanted is twelve bytes against twenty-four -- a size error to refuse,
        not a dtype to convert.
        """
        pytest.importorskip('numpy')
        glVertex3dv(np.zeros(3, 'f'))
        glVertex3dv(np.zeros(3, 'i'))

    def test_sequences_are_converted(self):
        glVertex3dv([1.0, 2.0, 3.0])
        glVertex3dv((1.0, 2.0, 3.0))

    def test_ctypes_arrays_are_accepted(self):
        glVertex3dv((ctypes.c_double * 3)(1.0, 2.0, 3.0))

    def test_memoryview_is_accepted(self):
        glVertex3dv(memoryview(np.zeros(3, 'd')))

    @needs_size_checking
    def test_too_short_is_refused_rather_than_read_past(self):
        """A wrongly sized array must raise, not hand the driver a short read.

        An empty sequence is the case that matters most: it converts to a
        zero-length array whose data pointer is null, and a size check that
        skipped null pointers would let the driver read from address zero.
        """
        for bad in ([], (), np.zeros(2, 'd'), np.zeros(0, 'd')):
            with pytest.raises((ValueError, TypeError)):
                glVertex3dv(bad)

    @needs_size_checking
    def test_too_long_is_refused(self):
        with pytest.raises((ValueError, TypeError)):
            glVertex3dv(np.zeros(4, 'd'))

    def test_none_is_a_null_pointer_where_one_is_meaningful(self):
        """An unbound client array is a null pointer, not an error."""
        glVertexPointer(3, GL_FLOAT, 0, None)


class TestArraysReachingTheEntryPoints(GLTestCase):
    """The array forms a caller actually passes, on the calls that take them.

    ``TestArrayAcceptance`` above asks what is accepted and refused at the
    boundary; this asks that the accepted forms reach the driver and do the
    thing.  Between them they cover the conversion in both directions -- the
    pointer handed down, and the array handed back.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_ctypes_array(self):
        color = (GLfloat * 3)(0, 1, 0)
        glColor3fv(color)

    @pytest.mark.skipif(
        OpenGL.ERROR_ON_COPY,
        reason='these forms are the ones that copy, which the flag refuses',
    )
    def test_pointers(self):
        """Test that basic pointer functions work"""
        vertex = GLdouble * 3
        vArray = vertex * 2
        glVertexPointerd([[2, 3, 4, 5], [2, 3, 4, 5]])
        glVertexPointeri(([2, 3, 4, 5], [2, 3, 4, 5]))
        glVertexPointers([[2, 3, 4, 5], [2, 3, 4, 5]])
        glVertexPointerd(vArray(vertex(2, 3, 4), vertex(2, 3, 4)))
        myVector = vArray(vertex(2, 3, 4), vertex(2, 3, 4))
        glVertexPointer(
            3, GL_DOUBLE, 0, ctypes.cast(myVector, ctypes.POINTER(GLdouble))
        )

        repr(glVertexPointerb([[2, 3], [4, 5]]))
        glVertexPointerf([[2, 3], [4, 5]])
        assert arrays.ArrayDatatype.dataPointer(None) == None
        glVertexPointerf(None)

        glNormalPointerd([[2, 3, 4], [2, 3, 4]])
        glNormalPointerd(None)

        glTexCoordPointerd([[2, 3, 4], [2, 3, 4]])
        glTexCoordPointerd(None)

        glColorPointerd([[2, 3, 4], [2, 3, 4]])
        glColorPointerd(None)

        glEdgeFlagPointerb([0, 1, 0, 0, 1, 0])
        glEdgeFlagPointerb(None)

        glIndexPointerd([0, 1, 0, 0, 1, 0])
        glIndexPointerd(None)

        glColor4fv([0, 0, 0, 1])

        # string data-types...
        s = struct.pack('>iiii', 2, 3, 4, 5) * 2
        glVertexPointer(4, GL_INT, 0, s)

    @pytest.mark.skipif(not np, reason="Numpy not available")
    def test_numpyConversion(self):
        """Test that we can run a numpy conversion from double to float for glColorArray"""
        a = np.arange(0, 1.2, 0.1, 'd').reshape((-1, 3))
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            glColorPointerf(a)
            glColorPointerd(a)
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)

    @pytest.mark.skipif(not np, reason="Numpy not available")
    def test_glbuffersubdata_numeric(self):
        from OpenGL.arrays import vbo

        assert vbo.get_implementation()
        points = np.array(
            [
                [0, 0, 0],
                [0, 1, 0],
                [1, 0.5, 0],
                [1, 0, 0],
                [1.5, 0.5, 0],
                [1.5, 0, 0],
            ],
            dtype='f',
        )
        d = vbo.VBO(points)
        with d:
            glBufferSubData(
                d.target,
                12,
                12,
                np.array([1, 1, 1], dtype='f'),
            )

    @pytest.mark.skipif(not np, reason="Numpy not available")
    @pytest.mark.skipif(OpenGL.ERROR_ON_COPY, reason="Test requires array copy")
    def test_copyNonContiguous(self):
        """Test that a non-contiguous (transposed) array gets applied as a copy"""
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        try:
            transf = np.identity(4, dtype=np.float32)
            # some arbitrary transformation...
            transf[0, 3] = 2.5
            transf[2, 3] = -80

            # what do we get with the un-transposed version...
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glMultMatrixf(transf)
            untransposed = glGetFloatv(GL_MODELVIEW_MATRIX)
            # now transposed...

            # with a copy it works...
            t2 = transf.transpose().copy()
            # This doesn't work:
            glLoadIdentity()
            glMultMatrixf(t2)
            # This does work:
            # glMultMatrixf(transf.transpose().copy())
            transposed = glGetFloatv(GL_MODELVIEW_MATRIX)

            assert not np.allclose(transposed, untransposed), (transposed, untransposed)

            t2 = transf.transpose()
            # This doesn't work:
            glLoadIdentity()
            glMultMatrixf(t2)
            # This does work:
            # glMultMatrixf(transf.transpose().copy())
            transposed = glGetFloatv(GL_MODELVIEW_MATRIX)

            assert not np.allclose(transposed, untransposed), (transposed, untransposed)
        finally:
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

    def test_bytes_array_support(self):
        color = b'\000' * 12
        glColor3fv(color)

    @pytest.mark.skipif(
        not (OpenGL.USE_ACCELERATE and acceleratesupport.ACCELERATE_AVAILABLE),
        reason="Need OpenGL_accelerate for buffer support",
    )
    def test_bytearray_support(self):
        import struct

        data = struct.pack(b'fff', 0.5, 0.4, 0.3)
        color = bytearray(data)
        glColor3fv(color)

    @pytest.mark.skipif(
        not (OpenGL.USE_ACCELERATE and acceleratesupport.ACCELERATE_AVAILABLE),
        reason="Need OpenGL_accelerate for buffer support",
    )
    def test_memoryview_support(self):
        color = bytearray(b'\000' * 12)
        mem = memoryview(color)
        glColor3fv(mem)

    def test_params_python3_strings(self):
        try:
            glGetUniformBlockIndex(0, unicode("Moo"))
        except ArgumentError:
            assert (
                OpenGL.ERROR_ON_COPY
            ), """Shouldn't have raised error on copy for unicode"""
        except TypeError:
            raise
        except GLError:
            # expected error, as we don't have a shader there...
            pass


if __name__ == '__main__':
    unittest.main()
