#! /usr/bin/env python3
"""Buffers made in one context of a shared pair, dropped while another is current.

Contexts created to share (``glfwCreateWindow``'s ``share``, ``eglCreateContext``'s
``share_context``) number their buffers together: a name made in one is the same
buffer in the other.  A program that loads on a worker thread with a context of
its own, and draws from a second, drops its ``VBO`` on whichever thread the
collector runs, with whichever of the two contexts is current there.

A ``VBO`` deletes its buffer only from a context that owns it.  Contexts that
share objects have one owner once the program has said so with
:func:`OpenGL.dispatch.share_context`; contexts that do not share number their
buffers separately, and a name from one is some other buffer in the other.

These cases create real contexts and ask the driver, with ``glIsBuffer``, what
was and was not deleted.
"""

import gc
import threading

import pytest

from OpenGL import dispatch, platform
from OpenGL.arrays import vbo
from OpenGL.GL import GL_ARRAY_BUFFER, glBindBuffer, glGenBuffers, glIsBuffer

from arraycompat import np
from glcontext import Context

POINTS = [[0, 0, 0], [0, 1, 0], [1, 0.5, 0]]


def current_handle():
    return platform.PLATFORM.GetCurrentContext()


@pytest.fixture
def contexts():
    """Contexts made by ``make``, released newest first when the case ends."""
    made = []

    def make(share_with=None):
        context = Context(
            profile='core', gl_version=(3, 3), share_with=share_with)
        made.append(context)
        context.make_current()
        return context

    yield make
    for context in reversed(made):
        context.release()


@pytest.fixture
def shared_pair(contexts):
    """Two contexts sharing objects, which PyOpenGL has been told about."""
    first = contexts()
    second = contexts(share_with=first)
    dispatch.share_context(second.handle, with_handle=first.handle)
    return first, second


@pytest.fixture
def unshared_pair(contexts):
    first = contexts()
    second = contexts()
    return first, second


def a_buffer():
    """A VBO whose buffer exists in the current context."""
    buffer = vbo.VBO(np.array(POINTS, 'f'))
    buffer.bind()
    buffer.unbind()
    assert glIsBuffer(int(buffer))
    return buffer


def collect():
    """Run the collector, so a VBO nothing refers to deletes its buffer now.

    The case deletes its own reference first: a name still bound to the VBO
    keeps it alive and the deleter never runs.
    """
    gc.collect()


def exists(name):
    return bool(glIsBuffer(name))


class TestAPairThatShares:
    def test_the_second_context_has_the_identity_of_the_first(self, shared_pair):
        first, second = shared_pair
        first.make_current()
        owner = dispatch.context_identity()
        second.make_current()
        assert dispatch.context_identity() is owner

    def test_a_buffer_dropped_in_the_other_context_is_deleted(self, shared_pair):
        first, second = shared_pair
        first.make_current()
        buffer = a_buffer()
        second.make_current()
        name = int(buffer)
        del buffer
        collect()
        assert not exists(name)
        first.make_current()
        assert not exists(name)

    def test_and_the_other_way_round(self, shared_pair):
        first, second = shared_pair
        second.make_current()
        buffer = a_buffer()
        first.make_current()
        name = int(buffer)
        del buffer
        collect()
        assert not exists(name)

    def test_a_buffer_dropped_in_its_own_context_is_deleted(self, shared_pair):
        first, _ = shared_pair
        first.make_current()
        buffer = a_buffer()
        name = int(buffer)
        del buffer
        collect()
        assert not exists(name)

    def test_a_buffer_outlives_the_context_that_made_it(self, contexts):
        """A loader's context is destroyed once it has loaded; what it made
        belongs to the context that draws it."""
        drawing = contexts()
        loader = contexts(share_with=drawing)
        dispatch.share_context(loader.handle, with_handle=drawing.handle)
        loader.make_current()
        buffer = a_buffer()
        loader.release()
        drawing.make_current()
        name = int(buffer)
        assert exists(name)
        del buffer
        collect()
        assert not exists(name)

    def test_a_buffer_dropped_on_another_thread_is_deleted_there(self, shared_pair):
        """The thread that collects the VBO has the second context current,
        and the first stays current on this one."""
        first, second = shared_pair
        first.make_current()
        holder = [a_buffer()]
        name = int(holder[0])
        failures = []

        def collect():
            try:
                second.make_current()
                holder.clear()
                gc.collect()
            except BaseException as err:  # noqa: BLE001 re-raised on the main thread below
                failures.append(err)

        worker = threading.Thread(target=collect)
        worker.start()
        worker.join()
        assert not failures
        assert not exists(name)


class TestAPairThatDoesNotShare:
    """Each context numbers its buffers from 1, so these are different buffers
    with the same name."""

    def test_a_buffer_is_left_alone_when_dropped_in_the_other_context(self, unshared_pair):
        first, second = unshared_pair
        first.make_current()
        buffer = a_buffer()
        second.make_current()
        name = int(buffer)
        del buffer
        collect()
        first.make_current()
        assert exists(name)

    def test_the_other_contexts_buffer_of_that_name_survives(self, unshared_pair):
        first, second = unshared_pair
        first.make_current()
        buffer = a_buffer()
        second.make_current()
        theirs = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, theirs)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        assert theirs == int(buffer)
        del buffer
        collect()
        assert exists(theirs)


class TestAPairThatSharesWithoutSayingSo:
    """PyOpenGL cannot see which contexts the application made to share."""

    def test_the_contexts_are_told_apart(self, contexts):
        first = contexts()
        second = contexts(share_with=first)
        first.make_current()
        owner = dispatch.context_identity()
        second.make_current()
        assert dispatch.context_identity() is not owner

    def test_a_buffer_dropped_in_the_other_context_is_left_alone(self, contexts):
        first = contexts()
        second = contexts(share_with=first)
        first.make_current()
        buffer = a_buffer()
        second.make_current()
        name = int(buffer)
        del buffer
        collect()
        first.make_current()
        assert exists(name)


class TestSharingIsPerContext:
    def test_a_context_outside_the_group_is_left_alone(self, shared_pair, contexts):
        first, second = shared_pair
        outsider = contexts()
        first.make_current()
        buffer = a_buffer()
        outsider.make_current()
        name = int(buffer)
        del buffer
        collect()
        first.make_current()
        assert exists(name)

    def test_a_context_made_where_a_destroyed_one_was_is_not_in_the_group(self, contexts):
        """The driver hands an address out again; being told a context is gone
        takes it out of its group, whatever lands on that address next."""
        first = contexts()
        second = contexts(share_with=first)
        gone = second.handle
        dispatch.share_context(gone, with_handle=first.handle)
        second.release()
        # Run until the driver hands the address out again, or give up: that
        # is a property of the driver, not of the library.
        for _ in range(64):
            fresh = contexts()
            if fresh.handle == gone:
                break
        else:
            pytest.skip('the driver did not reuse the address of a destroyed context')
        first.make_current()
        owner = dispatch.context_identity()
        fresh.make_current()
        assert dispatch.context_identity() is not owner
