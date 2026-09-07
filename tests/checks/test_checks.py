"""Run the stand-alone check scripts, and report what each of them said.

A check script is a program rather than a test case: it opens a window, drives
a toolkit's main loop, or settles a question that can only be asked once per
process, and it says how it went by what it prints and the status it exits
with.  ``OK`` on stdout is a pass, exit status 77 is a skip
(``checkutils.skip``), and no output at all is a failure -- which is how the
harness tells a working check from one that died on an import or a null entry
point.

**The scripts are discovered, not listed.** Every ``check_*.py`` beside this
file is run.  A script that lists what it needs but is never run is the shape
this replaced: ``check_autocomplete.py`` and
``check_querier_version_parse.py`` sat here for years under a runner that
enumerated its scripts by hand, and neither was ever launched.

A script says what it needs in a ``# requires:`` line in its first few lines::

    # requires: glut numpy

which is read out of the file rather than imported, since importing it is the
thing being tested.  The vocabulary is :data:`REQUIREMENTS`; an unknown word is
an error rather than a silent pass, so a typo cannot turn into a check that
never runs.
"""

import glob
import logging
import os
import re
import subprocess
import sys

import pytest

import backends
import paths
from checkutils import SKIP_EXIT_CODE

HERE = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger(__name__)

WAYLAND = os.environ.get('XDG_SESSION_TYPE') == 'wayland'

#: How long one check script may take before it is killed and the case fails.
#:
#: These open a window and talk to a driver, so any of them can wait forever on
#: a machine none of us can log into: a GLUT window that never maps, a driver
#: waiting on a compositor that will not answer.  Without a limit that is not a
#: failed case but a job that runs until the whole run is cancelled, saying
#: nothing about which script it was waiting for.  Generous, because the point
#: is to bound a hang rather than to time anything: the slowest of these takes
#: about five seconds on a software rasteriser.
CHECK_TIMEOUT = float(os.environ.get('TEST_CHECK_TIMEOUT', '120'))

#: ``# requires: a b c`` anywhere in the first lines of a script.
_REQUIRES = re.compile(r'^#\s*requires:\s*(.*)$', re.M)

#: How many lines of a script are read looking for that line.
_HEADER_LINES = 40


def _numpy_installed():
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def _window_server():
    """Somewhere to open a window on, that the scripts can actually use.

    Wayland counts as nowhere here.  These are X11 and GLUT programs: raw Xlib
    calls have no Wayland equivalent, and GLUT's support for it is poor enough
    that a window either does not appear or does not answer.  Under a compositor
    the run wants ``xvfb-run``, which is what the Linux CI job does.
    """
    if WAYLAND:
        return 'GLUT and raw X11 have no usable Wayland path; run under xvfb-run'
    if not backends.has_window_server():
        # A machine with the libraries but nowhere to draw.  freeglut answers a
        # display it cannot open by writing to stderr and calling exit(), which
        # reaches the harness as a script that produced no output rather than
        # as the absent display it is.
        return 'no display server to open a window on'
    return None


def _glut():
    from OpenGL.GLUT import glutInit

    if not glutInit:
        return 'no GLUT installed'
    return None


def _linux():
    if not sys.platform.startswith('linux'):
        return 'Linux only'
    return None


#: What a ``# requires:`` word means, as a function answering the reason it is
#: not satisfied (or ``None``).  ``implies`` chains them, so ``glx`` need not
#: restate that raw X11 needs a window server.
REQUIREMENTS = {
    'numpy': (lambda: None if _numpy_installed() else 'no numpy installed', ()),
    'window-server': (_window_server, ()),
    'xlib': (lambda: None, ('window-server',)),
    'glx': (_linux, ('xlib',)),
    'glut': (_glut, ('window-server',)),
}


def requirements_of(path):
    """The words in a script's ``# requires:`` line, as a list.

    Read from the file rather than imported: whether the script imports at all
    is part of what running it answers.
    """
    with open(path, encoding='utf-8') as handle:
        header = ''.join(handle.readlines()[:_HEADER_LINES])
    found = _REQUIRES.search(header)
    if not found:
        return []
    return found.group(1).replace(',', ' ').split()


def unsatisfied(names):
    """Why ``names`` cannot be satisfied here, or ``None``.

    An unknown word raises: a requirement nobody implements would otherwise be
    a check that quietly always runs, or quietly never does.
    """
    seen = set()
    pending = list(names)
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        if name not in REQUIREMENTS:
            raise KeyError(
                '%r is not one of the requirements a check script may ask for '
                '(%s)' % (name, ', '.join(sorted(REQUIREMENTS)))
            )
        answer, implies = REQUIREMENTS[name]
        pending.extend(implies)
        reason = answer()
        if reason:
            return reason
    return None


def scripts():
    """Every check script beside this file, by name, sorted."""
    return sorted(
        os.path.basename(path)
        for path in glob.glob(os.path.join(HERE, 'check_*.py'))
    )


def run_check(filename):
    """Run one script and return ``(returncode, stdout, stderr)``."""
    # These are stand-alone *windowed* scripts, and a headless backend has no
    # equivalent for them -- egl brings PYOPENGL_PLATFORM=egl and no window,
    # cgl has no window server to ask.  Run them in the default windowed mode
    # rather than propagating one, since a child that skipped would produce no
    # output and read here as a failure.
    env = dict(os.environ)
    if backends.is_headless(backends.requested(env)):
        env.pop('TEST_WINDOWING', None)
    # The scripts import the suite's helpers -- checkutils, testdecorator,
    # glcontext -- by bare name.  `pythonpath` in pyproject.toml puts tests/ on
    # the path of the *pytest* process; a child gets only its own directory,
    # which is this one, so it is named here.
    env['PYTHONPATH'] = os.pathsep.join(
        [paths.TESTS] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else [])
    )
    pipe = subprocess.Popen(
        [sys.executable, os.path.join(HERE, filename)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        stdout, stderr = pipe.communicate(timeout=CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        pipe.kill()
        stdout, stderr = pipe.communicate()
        raise AssertionError(
            '%s did not finish within %d seconds, and was killed.\n'
            'stdout: %s\nstderr: %s'
            % (
                filename,
                CHECK_TIMEOUT,
                stdout.decode('utf-8', errors='ignore').strip(),
                stderr.decode('utf-8', errors='ignore').strip(),
            )
        ) from None
    return (
        pipe.returncode,
        stdout.decode('utf-8', errors='ignore'),
        stderr.decode('utf-8', errors='ignore'),
    )


@pytest.mark.parametrize('filename', scripts())
def test_the_check_script_says_it_worked(filename):
    reason = unsatisfied(requirements_of(os.path.join(HERE, filename)))
    if reason:
        pytest.skip('%s: %s' % (filename, reason))

    log.info('Starting check: %s', filename)
    returncode, stdout, stderr = run_check(filename)

    if returncode == SKIP_EXIT_CODE:
        pytest.skip(
            'the script signalled skip: %s' % (stdout.strip() or stderr.strip(),)
        )
    lines = [line.strip() for line in stdout.strip().splitlines()]
    if not lines:
        raise AssertionError(
            '%s produced no output, which is how a script that died on an '
            'import or a null entry point looks.\nstderr: %s'
            % (filename, stderr.strip())
        )
    if 'SKIP' in lines:
        pytest.skip('the script skipped itself: %s' % (stdout.strip(),))
    if 'OK' not in lines:
        raise AssertionError(
            '%s did not print OK.\nstdout: %s\nstderr: %s'
            % (filename, stdout.strip(), stderr.strip())
        )


class TestTheScriptsAreDiscovered:
    """The discovery itself, since a runner that finds nothing passes."""

    def test_there_are_scripts_to_run(self):
        assert len(scripts()) > 10, scripts()

    @pytest.mark.parametrize('filename', scripts())
    def test_every_script_asks_for_requirements_that_exist(self, filename):
        """A typo in a ``# requires:`` line is an error, not a silent skip."""
        names = requirements_of(os.path.join(HERE, filename))
        for name in names:
            assert name in REQUIREMENTS, (filename, name)

    def test_an_unknown_requirement_is_refused(self):
        with pytest.raises(KeyError):
            unsatisfied(['not-a-requirement'])
