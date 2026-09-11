"""What a VBO's deleter does when it runs somewhere GL cannot be called

A deleter is a weakref callback, so it runs wherever the collector happened to
be.  In a program that loads its data on a worker thread -- which is the usual
shape of anything that shows a model without freezing -- that is as likely as
not a thread with no GL context current on it at all.  Buffer names belong to
the context that made them, so deleting one from there cannot work: the call
either does nothing or, on some drivers, takes the process down.

Nor can it be deleted from a *different* context.  Every context numbers its
buffers from 1, so a name from one context is, in another, that context's own
buffer of the same number -- and deleting it takes the vertex data out from
under whatever the other context draws next.  A deleter that runs while some
other context is current, or one that has taken over the handle of the context
that made the buffer, lets the names go instead.
"""

import pytest

from OpenGL import dispatch
from OpenGL.arrays import vbo


class Recorder(vbo.Implementation):
    """An Implementation that records deletions instead of making them"""

    def __init__(self):
        self.deleted = []

    def glDeleteBuffers(self, count, buffer):
        self.deleted.append(int(buffer.value))


@pytest.fixture
def current(monkeypatch):
    """Choose the current GL context, as the platform and the dispatch layer
    both report it, starting from no context PyOpenGL has seen before"""
    monkeypatch.setattr(dispatch, '_identities', {}, raising=False)

    def choose(handle):
        monkeypatch.setattr(vbo.platform, 'GetCurrentContext', lambda: handle)
        monkeypatch.setattr(dispatch, '_current_context', lambda: handle)

    return choose


def made_in(current, handle):
    """The context `handle` names, as a VBO made there records it"""
    current(handle)
    return dispatch.context_identity()


def test_buffers_are_deleted_in_the_context_that_made_them(current):
    owner = made_in(current, 0x1234)
    implementation = Recorder()
    implementation.deleter([7, 8], key='k', owner=owner)()
    assert sorted(implementation.deleted) == [7, 8]


def test_nothing_is_deleted_in_a_context_that_did_not_make_them(current):
    """In that context these names are its own buffers."""
    owner = made_in(current, 0x1234)
    current(0x5678)
    implementation = Recorder()
    buffers = [7, 8]
    implementation.deleter(buffers, key='k', owner=owner)()
    assert implementation.deleted == []
    assert buffers == []


def test_nor_in_one_that_has_taken_over_its_handle(current):
    """A destroyed context's address is handed out again, and forget_context is
    how PyOpenGL is told the context at that address is no longer the same."""
    owner = made_in(current, 0x1234)
    dispatch.forget_context(0x1234)
    implementation = Recorder()
    implementation.deleter([7, 8], key='k', owner=owner)()
    assert implementation.deleted == []


def test_nothing_is_deleted_with_no_context_current(current):
    """The call cannot free anything, and on some drivers it is fatal."""
    owner = made_in(current, 0x1234)
    current(0)
    implementation = Recorder()
    implementation.deleter([7, 8], key='k', owner=owner)()
    assert implementation.deleted == []


def test_the_names_are_let_go_of_either_way(current):
    """They are freed with the context that owns them, so holding on to them
    would leak the list and re-run the same impossible call."""
    owner = made_in(current, 0x1234)
    current(0)
    implementation = Recorder()
    buffers = [7, 8]
    implementation.deleter(buffers, key='k', owner=owner)()
    assert buffers == []


def test_the_deleter_deregisters_itself(current):
    owner = made_in(current, 0x1234)
    implementation = Recorder()
    implementation._DELETERS_['k'] = object()
    implementation.deleter([7], key='k', owner=owner)()
    assert 'k' not in implementation._DELETERS_


def test_the_deleter_deregisters_itself_with_no_context_either(current):
    """Otherwise a program that closes its window keeps every deleter it ever
    made, for buffers that no longer exist."""
    owner = made_in(current, 0x1234)
    current(0)
    implementation = Recorder()
    implementation._DELETERS_['k'] = object()
    implementation.deleter([7], key='k', owner=owner)()
    assert 'k' not in implementation._DELETERS_
