"""The environment a test gives a child process it spawns.

Several suites run a fragment of PyOpenGL in a fresh interpreter, because what
they are checking is settled once per process: which dispatch implementation is
installed, what an import costs, whether a call without a context is refused.
Those children pin a platform so that the child does not choose a different one
from the parent and answer a different question.

**Which platform is pinned is incidental to every one of them.** GLX is what an
X11 machine has, and naming it directly makes the suite unrunnable anywhere
else: on Windows the child loads a platform with no library behind it, every
entry point resolves to null, and the child dies on its first call rather than
reaching the report it was spawned for -- which reads as a failure of the thing
under test rather than an absent platform.

A test *about* GLX is a different matter and skips outright; see
``tests/test_glx_raw_x.py``, which refuses to run off Linux at module level.
"""

import os
import sys

#: Platforms that have no GLX and must be left to choose for themselves.
#: Windows resolves to WGL, macOS to its own; both are what the machine has.
_CHOOSES_ITS_OWN = ('win32', 'darwin')


def child_environment(**overrides):
    """A copy of this process's environment, for a child that loads OpenGL.

    Pins ``PYOPENGL_PLATFORM`` to GLX where GLX is what the machine offers, and
    leaves it unset where it is not, so the child detects the platform it
    actually has. An ambient setting always wins: a run that has already chosen
    a platform means it, and these are not the place to overrule it.

    `overrides` are applied last, for a test that needs to say something else.
    """
    environment = dict(os.environ)
    if sys.platform not in _CHOOSES_ITS_OWN:
        environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    environment.update(overrides)
    return environment
