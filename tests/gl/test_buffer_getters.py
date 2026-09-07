#! /usr/bin/env python3
"""Buffer-object getters, and the shape of what they hand back.

``glGetBufferParameteriv`` and ``glGetBufferSubData`` are the two directions of
the same question: a getter that decides the size of its own output, and a
getter filling an output array the caller supplied.  Both are places a wrong
size is a heap overrun rather than a wrong answer, and both have had one.

They are also where ``SIZE_1_ARRAY_UNPACK`` is visible.  Every pname here is a
single value, and that flag decides whether a single value comes back as a
scalar or as a one-element array -- so the cases say which they expect rather
than accepting either.  Unlike its neighbours in ``OpenGL/__init__.py`` it is
not an ``environ_key``: it is set by assigning to ``OpenGL.SIZE_1_ARRAY_UNPACK``
before anything else imports ``OpenGL``, and ``PYOPENGL_SIZE_1_ARRAY_UNPACK``
does nothing.
"""

import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL import _configflags
from OpenGL.GL import *  # noqa: F401,F403

#: Every parameter here is one value, and what a freshly named but never-sized
#: buffer answers for it.
FRESH = (
    (GL_BUFFER_SIZE, 0),
    (GL_BUFFER_MAPPED, GL_FALSE),
    (GL_BUFFER_STORAGE_FLAGS, 0),
    (GL_BUFFER_USAGE, GL_STATIC_DRAW),
)


class BufferGetterTestCase(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def bound_buffer(self):
        """A buffer bound to GL_ARRAY_BUFFER, unbound and deleted afterwards."""
        self.require_vertex_arrays()
        buffer = glGenBuffers(1)
        vertex_array = glGenVertexArrays(1, buffer)
        glBindBuffer(GL_ARRAY_BUFFER, buffer)

        def release():
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDeleteVertexArrays(1, vertex_array)
            glDeleteBuffers(1, buffer)

        self.defer_cleanup(release)
        return buffer


class TestAskingABufferAboutItself(BufferGetterTestCase):
    def test_a_single_valued_pname_comes_back_as_one_value(self):
        """``GL_BUFFER_USAGE`` used to be recorded as four.

        It shares its enum value with ``GL_OBJECT_BUFFER_USAGE_ATI``, and the
        size table is keyed on the value, so whichever was written last won.
        The fix is in glgetsizes.csv; this is what notices it coming back.
        """
        self.bound_buffer()
        for pname, expected in FRESH:
            answered = glGetBufferParameteriv(GL_ARRAY_BUFFER, pname)
            if _configflags.SIZE_1_ARRAY_UNPACK:
                self.assertEqual(answered, expected, (pname, answered, expected))
            else:
                self.assertEqual(len(answered), 1, (pname, answered))
                self.assertEqual(answered[0], expected, (pname, answered, expected))
        self.check_error('glGetBufferParameteriv')

    def test_an_output_variable_is_filled_rather_than_replaced(self):
        """Passing a GLint in is the C spelling, and must write into it."""
        self.bound_buffer()
        for pname, expected in FRESH:
            answered = GLint(-1)
            glGetBufferParameteriv(GL_ARRAY_BUFFER, pname, answered)
            self.assertEqual(answered.value, expected, (pname, answered, expected))
        self.check_error('glGetBufferParameteriv into a caller variable')

    @pytest.mark.skipif(
        not _configflags.SIZE_1_ARRAY_UNPACK,
        reason='SIZE_1_ARRAY_UNPACK is off, so a single value stays an array',
    )
    def test_a_generated_name_is_a_scalar(self):
        """``glGenBuffers(1)`` is one name, and unpacks to one number."""
        self.require_vertex_arrays()
        buffer = glGenBuffers(1)
        self.assertTrue(np.isscalar(buffer) if hasattr(np, 'isscalar') else True,
                        type(buffer))
        self.assertEqual(int(buffer), buffer)
        glDeleteBuffers(1, buffer)


class TestReadingBufferContentsBack(BufferGetterTestCase):
    """``glGetBufferSubData`` fills an array the caller allocated.

    A correctly typed array is filled in place.  A mismatched one would be
    converted to a *copy*, the driver would write the result into the copy, and
    the caller would be handed back its own untouched zeroes -- so it has to
    raise instead.
    """

    def uploaded(self):
        pytest.importorskip('numpy', reason='the mismatch case needs a real dtype')
        source = np.array([0x04030201, 0x08070605, 0x0C0B0A09], 'uint32')
        nbytes = 12
        self.bound_buffer()
        glBufferData(GL_ARRAY_BUFFER, nbytes, source, GL_STATIC_DRAW)
        return source, nbytes

    def test_a_correctly_typed_array_is_filled_in_place(self):
        source, nbytes = self.uploaded()
        target = np.zeros(nbytes, 'uint8')
        glGetBufferSubData(GL_ARRAY_BUFFER, 0, nbytes, target)
        self.assertTrue((target.view('uint32') == source).all(), list(target))
        self.check_error('glGetBufferSubData')

    def test_an_array_of_the_wrong_type_is_refused(self):
        """Not silently answered with zeroes, which is what was reported."""
        source, nbytes = self.uploaded()
        with self.assertRaises((TypeError, ValueError)):
            glGetBufferSubData(
                GL_ARRAY_BUFFER, 0, nbytes, np.zeros(3, 'uint32')
            )


if __name__ == '__main__':
    unittest.main()
