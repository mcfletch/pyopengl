#! /usr/bin/env python3
"""What a call takes hold of, it gives back.

An entry point acquires the caller's arrays and strings for the duration of
the call, and hands back objects of its own making.  Both directions are
counted here, because a reference miscounted either way is invisible until it
has accumulated:

* An argument's buffer.  ``PyObject_GetBuffer`` raises the exporter's export
  count and takes a reference to it, and failing to release the buffer leaks
  both.  The error paths are what make this worth asserting: a call that
  acquires one array and then fails converting a second must still release the
  first, and functions taking two arrays are ordinary.
* A char ** built over a list of strings, which owns the bytes objects the
  pointers point into for exactly as long as the driver is reading them.
* A returned value -- bytes, an address, an opaque handle, an output array --
  which the caller must end up holding alone.
* An array registered against the context, which outlives the call by design
  and so has to be given back when the registration is replaced.
"""

import contextlib
import ctypes
import gc
import sys
import unittest
import weakref

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL import _configflags
from OpenGL import _dispatch


def own(text):
    """A string equal to `text` that this process built, rather than interned.

    ``sys.getrefcount`` of a literal counts the references the whole process
    holds to the one interned object, so a count taken around a call reports
    whatever else happened to name the same string.  And from Python 3.12 such
    a literal is immortal (PEP 683): its count is a fixed sentinel that never
    moves, so an assertion about it cannot fail and cannot pass for a reason.
    Neither is true of a string built here, which is the only kind worth
    counting.
    """
    return ''.join(text)


@contextlib.contextmanager
def no_references_kept(*objects):
    """Assert the block gives back every reference it took to `objects`.

    For an array argument that means no buffer of it is still held:
    ``PyObject_GetBuffer`` takes a reference to the exporter and
    ``PyBuffer_Release`` hands it back, so a buffer acquired and not released
    shows as a reference the array did not have going in.  That reference is
    what there is to see: a numpy array with a live export used to refuse to
    have its shape set, which is what this asked before, and from numpy 2.5 it
    no longer does -- so the question had stopped being asked at all.  For a
    list of strings it means the same of the list and of the bytes built from
    it.

    Both counts are read by the same expression, because ``getrefcount`` sees
    whatever the reading itself is holding -- a loop that unpacks the objects
    differently from the comprehension that counted them reports the machinery
    rather than the call.
    """
    before = [sys.getrefcount(item) for item in objects]
    yield
    gc.collect()
    after = [sys.getrefcount(item) for item in objects]
    assert after == before, (
        'references taken during the call and not given back: %r'
        % ([a - b for a, b in zip(after, before)],)
    )


def clean_reading():
    """What ``getrefcount`` answers for a value one local holds and nothing else.

    Two through Python 3.13 -- the local, and the argument the call is handed --
    and one from 3.14, which does not take a reference for that argument.  So it
    is measured rather than written down, in the same shape
    :func:`call_and_count` reads in: a value bound to one local, counted by name.
    Whatever the interpreter's convention, the difference cancels.
    """
    value = [1, 2, 3]
    return sys.getrefcount(value)


def call_and_count(call):
    """Run `call`, and say how many references its result has beyond the one.

    Zero where the conversion kept nothing back, and one per call leaked where
    it did not.  The counting happens here rather than in the test, because a
    count read in the caller's frame includes whatever the caller is holding:
    an assertion rewritten by pytest binds the value it is about to describe,
    and a registered cleanup keeps it for the length of the test.

    The count goes into a local of its own before anything is built from it:
    ``return value, sys.getrefcount(value)`` would push `value` as the first
    element of the tuple before counting it, and report one reference more than
    exists.
    """
    value = call()
    count = sys.getrefcount(value)
    return value, count - clean_reading()


class TestTheCounting(unittest.TestCase):
    """The two instruments above, against a reference deliberately kept.

    Every assertion in this file is a number that should not move, and a
    reading that cannot move is a test that passes whatever the code does.
    These say what a kept reference looks like, so the rest mean something.
    No GL is involved.
    """

    def test_a_kept_reference_is_noticed(self):
        held = []
        values = [1, 2, 3]
        with pytest.raises(AssertionError):
            with no_references_kept(values):
                held.append(values)

    def test_a_result_with_a_reference_kept_is_counted(self):
        held = []

        def make_and_keep():
            value = [1, 2, 3]
            held.append(value)
            return value

        _, extra = call_and_count(make_and_keep)
        assert extra == 1

    def test_a_result_nobody_kept_counts_none(self):
        _, extra = call_and_count(lambda: [1, 2, 3])
        assert extra == 0


class TestBufferLifetime(GLTestCase):
    profile = 'compat'

    def test_a_successful_call_releases_its_buffer(self):
        values = np.zeros(3, 'd')
        with no_references_kept(values):
            glVertex3dv(values)

    @pytest.mark.skipif(
        not _configflags.ARRAY_SIZE_CHECKING,
        reason='ARRAY_SIZE_CHECKING is off, so there is no size check to fail',
    )
    def test_a_failing_size_check_releases_its_buffer(self):
        values = np.zeros(4, 'd')
        with no_references_kept(values):
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
        with no_references_kept(first, count):
            glMultiDrawArrays(GL_TRIANGLES, first, count, 0)

    def test_a_failure_after_a_successful_acquisition_releases_it(self):
        """The first array is acquired; the second cannot be converted.

        This is the case the cleanup frame exists for: without it the first
        buffer stays exported for the life of the array.
        """
        first = np.zeros(2, 'i')
        with no_references_kept(first):
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
        with no_references_kept(into):
            # Not bound to a name: what comes back *is* the array, so holding
            # it would be a reference the block is entitled to see.
            assert glGenTextures(4, into) is into


def char_pp(strings):
    """The ``char **`` a caller builds when they build it themselves."""
    block = (ctypes.c_char_p * len(strings))(*[text.encode() for text in strings])
    return ctypes.cast(block, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class VaryingsTestCase(GLTestCase):
    """A program to record transform-feedback varying names against.

    Recording them is what ``glTransformFeedbackVaryings`` does; linking is
    what would read them back, and none of these tests needs it.
    """

    profile = 'compat'
    gl_version = (3, 0)

    def setUp(self):
        super().setUp()
        self.program = glCreateProgram()
        self.addCleanup(glDeleteProgram, self.program)


class TestStringArrayLifetime(VaryingsTestCase):
    """An array of pointers the caller assembled is borrowed, not kept.

    The count is not asserted to be unchanged here, and the reason is
    ``ctypes`` rather than anything in the entry point: reading an address off
    a ctypes pointer casts it, and a cast records its source in the source's
    own ``_objects``.  That self-reference is what the first call adds, the
    cycle collector is what takes it away, and neither is per-call -- so what
    is asserted is that nothing accumulates and that the pointer dies with the
    caller's last reference to it.
    """

    def test_repeating_the_call_does_not_accumulate(self):
        names = char_pp(['position', 'colour'])
        glTransformFeedbackVaryings(self.program, 2, names, GL_SEPARATE_ATTRIBS)
        gc.collect()
        after_one = sys.getrefcount(names)
        for _ in range(100):
            glTransformFeedbackVaryings(self.program, 2, names, GL_SEPARATE_ATTRIBS)
        gc.collect()
        assert sys.getrefcount(names) == after_one

    def test_the_pointer_array_does_not_outlive_the_caller(self):
        def use_it():
            names = char_pp(['position', 'colour'])
            glTransformFeedbackVaryings(self.program, 2, names, GL_SEPARATE_ATTRIBS)
            return weakref.ref(names)

        died = use_it()
        gc.collect()
        assert died() is None


class TestStringListLifetime(VaryingsTestCase):
    """A char ** assembled for the caller over the strings they passed.

    Whichever implementation is running builds the array of pointers and owns
    the bytes they point into for the length of the call: the C layer in
    ``pygl_string_array``, the ctypes bindings in the argument type the
    declaration is built with.  Neither may still hold them afterwards.
    """

    def test_a_list_of_names_is_given_back(self):
        names = [own(name) for name in ('position', 'colour')]
        with no_references_kept(names, names[0], names[1]):
            glTransformFeedbackVaryings(
                self.program, len(names), names, GL_SEPARATE_ATTRIBS
            )

    def test_one_name_on_its_own_is_given_back(self):
        """A single string is a list of one, and callers pass it that way."""
        name = own('position')
        with no_references_kept(name):
            glTransformFeedbackVaryings(self.program, 1, name, GL_SEPARATE_ATTRIBS)

    def test_a_name_that_is_not_a_string_gives_back_what_it_took(self):
        """The list is walked, so the refusal comes with entries already held.

        Whatever was converted before the bad entry has to be released on the
        way out, which is the same obligation the array frame has and a
        different piece of code.
        """
        names = [own('position'), 42]
        with no_references_kept(names, names[0]):
            # ctypes wraps what a conversion raises in its own ArgumentError,
            # so which exception carries the refusal depends on the
            # implementation; that both refuse is asserted in test_string_arrays.
            with pytest.raises((TypeError, ctypes.ArgumentError)):
                glTransformFeedbackVaryings(
                    self.program, len(names), names, GL_SEPARATE_ATTRIBS
                )

    def test_repeating_the_call_does_not_accumulate(self):
        """A hundred calls hold no more than one does.

        Through :func:`no_references_kept` rather than a count either side: the
        second reading was inside an ``assert``, which pytest rewrites into
        temporaries that hold the object while it is counted, so it read one
        higher than the plain assignment before the loop and reported a leak of
        exactly one on a call that leaks none.
        """
        names = [own(name) for name in ('position', 'colour')]
        with no_references_kept(names[0], names[1]):
            for _ in range(100):
                glTransformFeedbackVaryings(
                    self.program, len(names), names, GL_SEPARATE_ATTRIBS
                )


class TestReturnedValues(GLTestCase):
    """Each return conversion hands the caller a reference and keeps none.

    One reference too many is a leak of the returned object on every call, and
    nothing about the value itself looks wrong -- which is why it is counted
    rather than inspected.
    """

    profile = 'compat'

    def test_a_returned_string_is_the_callers_alone(self):
        vendor, extra = call_and_count(lambda: glGetString(GL_VENDOR))
        assert isinstance(vendor, bytes)
        assert extra == 0

    def test_a_returned_output_array_is_the_callers_alone(self):
        names, extra = call_and_count(lambda: glGenTextures(4))
        self.addCleanup(glDeleteTextures, names)
        assert extra == 0

    def test_a_returned_scalar_output_is_the_callers_alone(self):
        """A one-element result is unpacked, so the array must not linger."""
        value, extra = call_and_count(lambda: glGetIntegerv(GL_MAX_TEXTURE_SIZE))
        assert int(value) > 0
        assert extra == 0

    def test_a_returned_address_is_the_callers_alone(self):
        """A mapped buffer comes back as the address itself."""
        buffers = glGenBuffers(1)
        self.addCleanup(glDeleteBuffers, 1, buffers)
        glBindBuffer(GL_ARRAY_BUFFER, buffers)
        self.addCleanup(glBindBuffer, GL_ARRAY_BUFFER, 0)
        glBufferData(GL_ARRAY_BUFFER, 64, None, GL_STATIC_DRAW)
        address, extra = call_and_count(
            lambda: glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
        )
        try:
            assert isinstance(address, int)
            assert extra == 0
        finally:
            glUnmapBuffer(GL_ARRAY_BUFFER)


class TestReturnedOpaqueHandle(GLTestCase):
    """A sync object comes back as an opaque handle built for the caller."""

    profile = 'core'
    gl_version = (3, 2)

    def test_a_returned_opaque_handle_is_the_callers_alone(self):
        sync, extra = call_and_count(
            lambda: glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
        )
        self.addCleanup(glDeleteSync, sync)
        assert extra == 0


class TestRetainedArrays(GLTestCase):
    """A client array outlives the call, and is given back when replaced.

    The GL goes on reading a client-side array after the call that registered
    it returns, so the reference the context holds is the point rather than a
    leak.  What makes it a leak is holding the previous one too.
    """

    profile = 'compat'

    def test_a_registered_array_is_held_by_the_context(self):
        values = np.zeros((4, 3), 'f')
        before = sys.getrefcount(values)
        glVertexPointer(3, GL_FLOAT, 0, values)
        gc.collect()
        assert sys.getrefcount(values) == before + 1

    def test_replacing_the_registration_gives_the_first_array_back(self):
        first = np.zeros((4, 3), 'f')
        second = np.zeros((4, 3), 'f')
        before_first = sys.getrefcount(first)
        glVertexPointer(3, GL_FLOAT, 0, first)
        before_second = sys.getrefcount(second)
        glVertexPointer(3, GL_FLOAT, 0, second)
        gc.collect()
        assert sys.getrefcount(first) == before_first
        assert sys.getrefcount(second) == before_second + 1

    def test_re_registering_the_same_array_holds_it_once(self):
        values = np.zeros((4, 3), 'f')
        before = sys.getrefcount(values)
        for _ in range(100):
            glVertexPointer(3, GL_FLOAT, 0, values)
        gc.collect()
        assert sys.getrefcount(values) == before + 1


if __name__ == '__main__':
    unittest.main()
