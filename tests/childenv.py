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
``tests/bindings/glx/``, which asks for a real X server.

:func:`run_in_child` and :func:`json_from_child` are the other half: the
plumbing every one of those tests otherwise writes for itself -- start in the
checkout, put the suite on the child's path, fail with what the child printed
rather than with a parse error on an empty string.
"""

import json
import os
import subprocess
import sys

import paths

#: Platforms that have no GLX and must be left to choose for themselves.
#: Windows resolves to WGL, macOS to its own; both are what the machine has.
_CHOOSES_ITS_OWN = ('win32', 'darwin')


def child_environment(**overrides):
    """A copy of this process's environment, for a child that loads OpenGL.

    Puts the suite's own directory on the child's path, and pins
    ``PYOPENGL_PLATFORM`` to GLX where GLX is what the machine offers, and
    leaves it unset where it is not, so the child detects the platform it
    actually has. An ambient setting always wins: a run that has already chosen
    a platform means it, and these are not the place to overrule it.

    `overrides` are applied last, for a test that needs to say something else.
    An override of ``None`` *removes* the variable, which is how a child is
    given a clean slate for one it must decide for itself -- the platform, when
    the interface it names is the thing being taken away.
    """
    environment = dict(os.environ)
    if sys.platform not in _CHOOSES_ITS_OWN:
        environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    # The suite's own directory, so a child can import checkutils, glcontext
    # and friends by bare name.  `pythonpath` in pyproject.toml puts them on
    # the *pytest* process's path; a child gets only its own directory.
    environment['PYTHONPATH'] = os.pathsep.join(
        [paths.TESTS]
        + [part for part in [environment.get('PYTHONPATH')] if part]
    )
    for key, value in overrides.items():
        if value is None:
            environment.pop(key, None)
        else:
            environment[key] = value
    return environment


#: How long a child gets before it is killed and the case fails.  Generous,
#: because the point is to bound a hang rather than to time anything: these
#: import PyOpenGL and sometimes open a context, which is under a second.
CHILD_TIMEOUT = 300


def run_in_child(source, check=True, timeout=CHILD_TIMEOUT, **environment):
    """Run ``source`` in a fresh interpreter and return the CompletedProcess.

    The child starts in the checkout, with the suite's own directory on its
    path so it can import the helpers by bare name -- ``pythonpath`` in
    ``pyproject.toml`` puts them on *this* process's path, and a child inherits
    only its own directory.

    ``check`` asserts the child exited zero, with its stderr as the message,
    which is what a test wants nine times in ten: a child that died reports as
    a failure naming what it printed rather than as a JSONDecodeError.  Pass
    ``check=False`` where a non-zero exit is the thing being asked about.
    """
    completed = subprocess.run(
        [sys.executable, '-c', source],
        capture_output=True,
        text=True,
        cwd=paths.ROOT,
        env=child_environment(**environment),
        timeout=timeout,
    )
    if check:
        assert completed.returncode == 0, (
            'the child exited %s\n--- stderr ---\n%s\n--- stdout ---\n%s'
            % (completed.returncode, completed.stderr[-4000:],
               completed.stdout[-2000:])
        )
    return completed


def json_from_child(source, **environment):
    """``run_in_child`` and parse the child's stdout as JSON.

    The child says what it found by printing one JSON object, which keeps the
    reporting out of the assertions: what a test reads is a dict, and what
    fails is the assertion about it rather than the parse.
    """
    completed = run_in_child(source, **environment)
    try:
        return json.loads(completed.stdout)
    except ValueError:
        raise AssertionError(
            'the child printed something other than JSON:\n%s\n--- stderr ---\n%s'
            % (completed.stdout[-2000:], completed.stderr[-2000:])
        ) from None
