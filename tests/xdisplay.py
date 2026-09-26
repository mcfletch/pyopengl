"""Whether ``$DISPLAY`` names an X server a client can open.

A case that asks a real X server something -- the GLX version, its extension
list -- has to know whether there is one. The name alone does not say: a
machine often carries a socket left behind by a server that has gone, or
something else listening where one used to be, and a case reading only the
name then fails for want of a server rather than saying it cannot be run here.

    import xdisplay

    @pytest.fixture
    def x_server():
        if not xdisplay.answers():
            pytest.skip('no X server answers $DISPLAY')

Asked from a fixture rather than a ``skipif``, so a run that selects none of
those cases opens no client, and the answer is kept for the process.

A connection rules out a display nothing serves. Where something does answer,
libX11's ``XOpenDisplay`` is called in a subprocess, which is the call GLX
starts from: being listened to is not being let in, and the authority a client
needs is the client's own business. A machine with no libX11 has no display a
GLX case can use.
"""

import functools
import os
import socket
import subprocess
import sys

#: Where a local X server's socket is, which is where a client looks for it.
SOCKETS = '/tmp/.X11-unix'

#: The first TCP port X displays are numbered from.
PORT = 6000

#: What is run to find out whether the display can be opened.  Exits 0 where
#: ``XOpenDisplay`` answers a display, 1 where it answers NULL, and 2 where
#: there is no libX11 to ask.
CLIENT = '''
import ctypes, ctypes.util, sys
library = ctypes.util.find_library('X11')
if library is None:
    sys.exit(2)
x11 = ctypes.CDLL(library)
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
display = x11.XOpenDisplay(None)
if not display:
    sys.exit(1)
x11.XCloseDisplay(display)
'''


@functools.lru_cache(maxsize=None)
def _answers(display, directory, timeout):
    if not listens(display, directory, min(timeout, 2.0)):
        return False
    return _opens(display, timeout)


def answers(name=None, directory=SOCKETS, timeout=30.0):
    """Whether a client can open ``name`` (by default ``$DISPLAY``)."""
    display = (os.environ.get('DISPLAY', '') if name is None else name).strip()
    return _answers(display, directory, timeout)


answers.cache_clear = _answers.cache_clear


def _opens(display, timeout):
    """Whether ``XOpenDisplay`` answers ``display`` in a process of its own."""
    try:
        opened = subprocess.run(
            [sys.executable, '-c', CLIENT], capture_output=True,
            timeout=timeout, env=dict(os.environ, DISPLAY=display))
    except (OSError, subprocess.SubprocessError):
        return False
    return opened.returncode == 0


def _local_addresses(directory, number):
    """Where a client looks for local display ``number``, in the order it looks.

    On Linux libxcb tries the abstract socket first, so a server reachable only
    there -- a container sharing the host's network but not its ``/tmp`` -- is
    still a server.
    """
    path = os.path.join(directory, 'X%d' % (number,))
    if sys.platform.startswith('linux'):
        return ['\0' + path, path]
    return [path]


def listens(display, directory=SOCKETS, timeout=2.0):
    """Whether anything is listening where ``display`` says a server would be."""
    host, colon, screen = display.rpartition(':')
    if not colon:
        return False
    try:
        number = int(screen.split('.')[0] or 0)
    except ValueError:
        return False
    if host and host != 'unix':
        try:
            with socket.create_connection((host, PORT + number), timeout):
                return True
        except (OSError, ValueError):
            return False
    for address in _local_addresses(directory, number):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            connection.settimeout(timeout)
            connection.connect(address)
            return True
        except (OSError, ValueError):
            continue
        finally:
            connection.close()
    return False
