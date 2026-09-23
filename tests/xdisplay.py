"""Whether ``$DISPLAY`` names an X server a client can open.

A case that asks a real X server something -- the GLX version, its extension
list -- has to know whether there is one. The name alone does not say: a
machine often carries a socket left behind by a server that has gone, or
something else listening where one used to be, and a case reading only the
name then fails for want of a server rather than saying it cannot be run here.

    from xdisplay import answers

    @pytest.mark.skipif(not answers(), reason='no X server answers $DISPLAY')
    class TestAgainstARealServer:
        ...

A connection rules out a display nothing serves. Where something does answer,
a client is opened to see whether it is a server this process may use -- being
listened to is not being let in, and the authority a client needs is the
client's own business. With no client to open, a display that accepts a
connection is taken at its word.
"""

import os
import socket
import subprocess
import sys

#: Where a local X server's socket is, which is where a client looks for it.
SOCKETS = '/tmp/.X11-unix'

#: The first TCP port X displays are numbered from.
PORT = 6000

#: What is run to find out whether the display can be opened: a client that
#: builds a window and takes it down again.
CLIENT = 'import tkinter; tkinter.Tk().destroy()'


def answers(name=None, directory=SOCKETS, timeout=30.0):
    """Whether a client can open ``name`` (by default ``$DISPLAY``)."""
    display = (os.environ.get('DISPLAY', '') if name is None else name).strip()
    if not listens(display, directory, min(timeout, 2.0)):
        return False
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return True
    try:
        opened = subprocess.run(
            [sys.executable, '-c', CLIENT], capture_output=True,
            timeout=timeout, env=dict(os.environ, DISPLAY=display))
    except (OSError, subprocess.SubprocessError):
        return False
    return opened.returncode == 0


def listens(display, directory=SOCKETS, timeout=2.0):
    """Whether anything is listening where ``display`` says a server would be."""
    host, colon, screen = display.rpartition(':')
    if not colon:
        return False
    try:
        number = int(screen.split('.')[0] or 0)
    except ValueError:
        return False
    try:
        if host and host != 'unix':
            with socket.create_connection((host, PORT + number), timeout):
                return True
        else:
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                connection.settimeout(timeout)
                connection.connect(os.path.join(directory, 'X%d' % number))
            finally:
                connection.close()
        return True
    except (OSError, ValueError):
        return False
