"""The native stack of a process stuck in a call that never returns.

``faulthandler`` shows the Python frames of a stall, and a stall in a window
system call is one Python frame, the ``ctypes`` call, with nothing in it to say
which call inside the OS library is waiting.  macOS's ``sample`` reads the
native stack of a running process, and a thread of this process can run it
while the main thread is blocked: ``ctypes`` releases the GIL for the length of
a call.

    with sample_if_stalled(30):
        something_that_may_not_return()
"""

import contextlib
import os
import subprocess
import sys
import threading


@contextlib.contextmanager
def sample_if_stalled(seconds, duration=3):
    """Print this process's native stacks if the block runs past ``seconds``

    A no-op off macOS, where there is no ``sample``.  The report goes to
    standard output, between lines that say what it is.
    """
    if sys.platform != 'darwin':
        yield
        return

    def sample():
        print('-- no progress for %s s; native stacks of pid %d'
              % (seconds, os.getpid()), flush=True)
        done = subprocess.run(
            ['sample', str(os.getpid()), str(duration)],
            capture_output=True, text=True, check=False, timeout=60)
        print(done.stdout or done.stderr, flush=True)
        print('-- end of native stacks', flush=True)

    timer = threading.Timer(seconds, sample)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()
