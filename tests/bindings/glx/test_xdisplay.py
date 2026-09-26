"""Whether the display a machine names is one a client can open.

A case that asks a real X server something has to know whether there is one,
and ``DISPLAY`` naming a server is not the same as a server being there: a
machine often carries a socket left behind by one that has gone, or something
else listening where one used to be.

Headless: sockets, a subprocess and a string.
"""
import ctypes.util
import socket
import sys
import threading

import pytest

import xdisplay

#: A display number nothing is expected to be serving.
NOBODY = 79

needs_libx11 = pytest.mark.skipif(
    ctypes.util.find_library('X11') is None, reason='no libX11 to open a display with'
)


def test_no_display_named_is_no_display():
    assert not xdisplay.answers('')
    assert not xdisplay.answers('   ')


def test_a_display_nothing_listens_on():
    assert not xdisplay.answers(':%d' % NOBODY)


def test_a_name_that_is_not_a_display():
    assert not xdisplay.answers('nonsense')
    assert not xdisplay.answers(':what')


def test_a_socket_left_behind_by_a_server_that_has_gone(tmp_path):
    path = tmp_path / ('X%d' % NOBODY)
    closed = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    closed.bind(str(path))
    closed.close()
    assert path.exists()
    assert not xdisplay.listens(':%d' % NOBODY, directory=str(tmp_path))


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='abstract sockets are Linux')
def test_a_server_on_the_abstract_socket_alone(tmp_path):
    """libxcb connects to ``@/tmp/.X11-unix/X<n>`` before the path.

    A container sharing the host's network namespace reaches the server there
    with no ``/tmp/.X11-unix`` directory of its own.
    """
    listening = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listening.bind('\0' + str(tmp_path / ('X%d' % NOBODY)))
        listening.listen(1)
        assert not (tmp_path / ('X%d' % NOBODY)).exists()
        assert xdisplay.listens(':%d' % NOBODY, directory=str(tmp_path))
    finally:
        listening.close()


def _tcp_display():
    """A listening TCP socket at the port an X display number maps to, and that number."""
    for number in range(NOBODY, NOBODY + 40):
        listening = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listening.bind(('127.0.0.1', xdisplay.PORT + number))
        except OSError:
            listening.close()
            continue
        listening.listen(1)
        return listening, number
    pytest.skip('no free port in the X display range')


@needs_libx11
def test_something_listening_that_is_not_a_server(tmp_path):
    """A connection is accepted and dropped, and a client cannot open a display.

    Over TCP, because a client and ``listens()`` then reach the same socket:
    a client looks for a local socket only where every X client does.
    """
    listening, number = _tcp_display()

    def hang_up():
        try:
            while True:
                connection, _address = listening.accept()
                connection.close()
        except OSError:
            return

    thread = threading.Thread(target=hang_up, daemon=True)
    thread.start()
    try:
        display = '127.0.0.1:%d' % (number,)
        assert xdisplay.listens(display)
        assert not xdisplay.answers(display, timeout=10.0)
    finally:
        listening.close()
        thread.join(5)


def test_an_answer_is_asked_once(monkeypatch):
    """Each case that needs a server asks, and the client is opened once."""
    opened = []
    monkeypatch.setattr(xdisplay, 'listens', lambda *args, **named: True)
    monkeypatch.setattr(
        xdisplay, '_opens', lambda display, timeout: opened.append(display) or True
    )
    xdisplay.answers.cache_clear()
    try:
        assert xdisplay.answers(':%d' % NOBODY)
        assert xdisplay.answers(':%d' % NOBODY)
        assert opened == [':%d' % NOBODY]
    finally:
        xdisplay.answers.cache_clear()
