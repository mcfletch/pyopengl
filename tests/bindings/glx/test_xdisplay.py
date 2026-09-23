"""Whether the display a machine names is one a client can open.

A case that asks a real X server something has to know whether there is one,
and ``DISPLAY`` naming a server is not the same as a server being there: a
machine often carries a socket left behind by one that has gone, or something
else listening where one used to be.

Headless: sockets, a subprocess and a string.
"""
import os
import socket
import subprocess
import sys

import pytest

import xdisplay

#: A display number nothing is expected to be serving.
NOBODY = 79


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
    assert not xdisplay.answers(':%d' % NOBODY, directory=str(tmp_path))


def test_something_listening_that_is_not_a_server_we_may_use(tmp_path):
    """A connection is accepted and a client still cannot open a window."""
    pytest.importorskip('tkinter')
    listening = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listening.bind(str(tmp_path / ('X%d' % NOBODY)))
        listening.listen(1)
        assert xdisplay.listens(':%d' % NOBODY, directory=str(tmp_path))
        assert not xdisplay.answers(':%d' % NOBODY, directory=str(tmp_path))
    finally:
        listening.close()


@pytest.mark.parametrize('display', [':0', ':1', ':%d' % NOBODY])
def test_it_says_what_a_client_finds(display):
    """Its answer is the answer a client gets, whatever this machine has."""
    pytest.importorskip('tkinter')
    opened = subprocess.run([sys.executable, '-c', xdisplay.CLIENT],
                            capture_output=True, timeout=60,
                            env=dict(os.environ, DISPLAY=display))
    assert xdisplay.answers(display) == (opened.returncode == 0)
