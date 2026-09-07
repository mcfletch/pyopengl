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

from arraycompat import np, object_names, one
from gltestcase import GLTestCase
import OpenGL
from OpenGL import acceleratesupport, arrays, error, _configflags
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

#: For the cases whose subject *is* the conversion: a Python sequence, or an
#: array of the wrong element type, is copied into a buffer of the right one.
#: ``ERROR_ON_COPY`` is a caller refusing exactly that, so under it there is no
#: conversion to assert -- what there is instead is
#: ``TestWhatARunThatRefusesCopiesGets`` below.
converts_by_copying = pytest.mark.skipif(
    _configflags.ERROR_ON_COPY,
    reason='ERROR_ON_COPY refuses the copy this case is about',
)


class TestArrayAcceptance(GLTestCase):
    profile = 'compat'

    def test_matching_dtype_is_accepted(self):
        glVertex3dv(np.zeros(3, 'd'))

    @converts_by_copying
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

    @converts_by_copying
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
        # A run that has refused implicit copies refuses the two sequences
        # before their size is looked at, which is the same outcome by a
        # different route -- CopyError rather than ValueError.
        for bad in ([], (), np.zeros(2, 'd'), np.zeros(0, 'd')):
            with pytest.raises((ValueError, TypeError, error.CopyError)):
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


class TestWhereTheResultGoes(GLTestCase):
    """A getter may allocate the result, or fill something the caller passed.

    Both are supported spellings of the same call, and they have to agree: a
    caller migrating from one to the other should not find the numbers change.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_generator_allocates_when_it_is_not_given_somewhere(self):
        self.require_vertex_arrays()
        allocated = one(glGenVertexArrays(1))
        self.assertTrue(int(allocated), 'no name was generated')
        glDeleteVertexArrays(1, object_names(int(allocated)))

    def test_a_generator_fills_a_variable_it_is_given(self):
        self.require_vertex_arrays()
        target = GLuint()
        returned = glGenVertexArrays(1, target)
        self.assertTrue(target.value, 'the caller variable was not written to')
        self.assertTrue(returned)
        glDeleteVertexArrays(1, object_names(int(target.value)))

    def test_a_getter_answers_the_same_either_way(self):
        allocated = glGetFloatv(GL_FOG_COLOR)
        given = (GLfloat * 4)()
        glGetFloatv(GL_FOG_COLOR, given)
        self.assertEqual(list(allocated), list(given))
        self.check_error('glGetFloatv')


class TestWhatARunThatRefusesCopiesGets(GLTestCase):
    """``ERROR_ON_COPY``: the caller has said it will not pay for a conversion.

    PyOpenGL copies a Python sequence into a buffer of the right element type,
    and converts an array whose type does not match.  Both are conveniences a
    program optimising its data path wants to be told about rather than have
    performed, which is what the flag is for -- and what it does had no test at
    the entry-point boundary at all.

    The flag is read while ``OpenGL/arrays/lists.py`` is being imported, so the
    decorator that raises is applied once per process: the two configurations
    are two cases, each skipping under the other.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    @pytest.mark.skipif(
        not _configflags.ERROR_ON_COPY, reason='the run allows copies'
    )
    def test_a_list_is_refused_rather_than_copied(self):
        with self.assertRaises(error.CopyError):
            glVertex3dv([1.0, 2.0, 3.0])

    @pytest.mark.skipif(
        not _configflags.ERROR_ON_COPY, reason='the run allows copies'
    )
    def test_the_message_says_what_to_pass_instead(self):
        """A caller reading it has to be able to act on it."""
        with self.assertRaises(error.CopyError) as caught:
            glVertex3dv([1.0, 2.0, 3.0])
        message = str(caught.exception)
        self.assertIn('ERROR_ON_COPY', message)
        self.assertIn('numpy', message)

    @pytest.mark.skipif(
        not _configflags.ERROR_ON_COPY, reason='the run allows copies'
    )
    def test_an_array_of_the_right_type_is_still_accepted(self):
        """The flag refuses conversions, not arrays: the fast path still works."""
        glVertex3dv(np.zeros(3, 'd'))
        glVertex3dv((ctypes.c_double * 3)(1.0, 2.0, 3.0))
        self.check_error('passing an array of the declared type')

    @converts_by_copying
    def test_without_it_the_same_list_is_accepted(self):
        glVertex3dv([1.0, 2.0, 3.0])
        self.check_error('passing a list where copies are allowed')


class TestAnOutputArrayIsMeasuredAgainstTheCount(GLTestCase):
    """``glGenTextures(n, array)`` writes ``n`` names, whatever ``array`` holds.

    The count and the array are separate arguments and nothing in the call ties
    them together, so an array shorter than the count is written past the end:
    not an exception but a heap overrun, which surfaces later somewhere
    unrelated.  ``tests/README.md`` calls this out as the recurring
    memory-corrupting class of bug, and it is why ``get_checked`` exists.

    Asserted here rather than in ``test_review_fixes.py``, which asks the same
    question of the C dispatch layer alone: the guard has to hold under
    whichever implementation is selected, and on the pure-ctypes path -- what a
    ``pip install PyOpenGL`` without a compiler runs -- there was none.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    #: Every form a caller might reasonably pass, since they reach the
    #: converter by different routes: an array of the declared type is used
    #: as-is, one of another type is converted, and a list is built into one.
    def short_arrays(self):
        yield 'declared type', np.zeros(4, 'I')
        yield 'converted type', np.zeros(4, 'i')
        yield 'list', [0, 0, 0, 0]

    def test_an_array_shorter_than_the_count_is_refused(self):
        for label, target in self.short_arrays():
            with self.subTest(passing=label):
                with self.assertRaises((ValueError, TypeError, error.CopyError)):
                    glGenTextures(64, target)

    def test_an_array_long_enough_is_accepted(self):
        """A larger buffer is a caller reusing one, which is ordinary."""
        target = np.zeros(64, 'I')
        glGenTextures(4, target)
        self.check_error('glGenTextures into a larger array')
        glDeleteTextures(4, target)

    def test_asking_for_none_still_allocates(self):
        allocated = glGenTextures(4)
        self.assertEqual(len(allocated), 4)
        glDeleteTextures(4, allocated)
        self.check_error('glGenTextures allocating its own array')


if __name__ == '__main__':
    unittest.main()
