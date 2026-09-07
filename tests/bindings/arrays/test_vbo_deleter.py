"""What a VBO's deleter does when it runs somewhere GL cannot be called

A deleter is a weakref callback, so it runs wherever the collector happened to
be.  In a program that loads its data on a worker thread -- which is the usual
shape of anything that shows a model without freezing -- that is as likely as
not a thread with no GL context current on it at all.  Buffer names belong to
the context that made them, so deleting one from there cannot work: the call
either does nothing or, on some drivers, takes the process down.
"""

import pytest

from OpenGL.arrays import vbo


class Recorder(vbo.Implementation):
    """An Implementation that records deletions instead of making them"""

    def __init__(self):
        self.deleted = []

    def glDeleteBuffers(self, count, buffer):
        self.deleted.append(int(buffer.value))


@pytest.fixture
def current(monkeypatch):
    """Choose what the platform reports as the current GL context"""

    def choose(handle):
        monkeypatch.setattr(vbo.platform, 'GetCurrentContext', lambda: handle)

    return choose


def test_buffers_are_deleted_while_a_context_is_current(current):
    current(0x1234)
    implementation = Recorder()
    buffers = [7, 8]
    implementation.deleter(buffers, key='k')()
    assert sorted(implementation.deleted) == [7, 8]


def test_nothing_is_deleted_with_no_context_current(current):
    """The call cannot free anything, and on some drivers it is fatal."""
    current(0)
    implementation = Recorder()
    implementation.deleter([7, 8], key='k')()
    assert implementation.deleted == []


def test_the_names_are_let_go_of_either_way(current):
    """They are freed with the context that owns them, so holding on to them
    would leak the list and re-run the same impossible call."""
    current(0)
    implementation = Recorder()
    buffers = [7, 8]
    implementation.deleter(buffers, key='k')()
    assert buffers == []


def test_the_deleter_deregisters_itself(current):
    current(0x1234)
    implementation = Recorder()
    implementation._DELETERS_['k'] = object()
    implementation.deleter([7], key='k')()
    assert 'k' not in implementation._DELETERS_


def test_the_deleter_deregisters_itself_with_no_context_either(current):
    """Otherwise a program that closes its window keeps every deleter it ever
    made, for buffers that no longer exist."""
    current(0)
    implementation = Recorder()
    implementation._DELETERS_['k'] = object()
    implementation.deleter([7], key='k')()
    assert 'k' not in implementation._DELETERS_
