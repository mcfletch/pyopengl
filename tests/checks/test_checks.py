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
from checkutils import SKIP_EXIT_CODE
from childenv import child_environment

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


#: Open the X display and say what it is.  Exits non-zero where it cannot be
#: opened, which is a display these programs cannot use either.
_X_DISPLAY_PROBE = r"""
from Xlib import display

connection = display.Display()
try:
    print('xwayland' if 'XWAYLAND' in set(connection.list_extensions())
          else 'usable')
finally:
    connection.close()
"""


def _x_display_is_usable():
    """Whether ``DISPLAY`` names an X server these programs can use.

    Asked of the display rather than of the login session.  The two differ
    exactly where it matters: under ``xvfb-run`` on a Wayland desktop the
    session is still Wayland while ``DISPLAY`` names an X server that GLUT and
    raw Xlib are perfectly happy with -- and skipping there is how twenty
    scripts came to run only on CI, which is the one place nobody sees them
    fail until afterwards.

    XWayland is the case to refuse: it is an X server, so it opens, but GLUT's
    support for it is poor enough that a window either does not appear or does
    not answer.  It says what it is by advertising the XWAYLAND extension.

    ``None`` where the question cannot be asked -- no python-xlib, no DISPLAY
    -- and the caller falls back to the session type.

    Asked in a child, and once: a connection that fails part-way leaves
    python-xlib holding an open socket it will not close, which reaches this
    suite as an unraisable ResourceWarning against whichever case happens to
    be tearing down.
    """
    if not os.environ.get('DISPLAY', '').strip():
        return None
    completed = subprocess.run(
        [sys.executable, '-c', _X_DISPLAY_PROBE],
        capture_output=True, text=True, timeout=30,
    )
    if completed.returncode != 0:
        return False
    answer = completed.stdout.strip()
    return {'usable': True, 'xwayland': False}.get(answer)


def _window_server():
    """Somewhere to open a window on, that the scripts can actually use.

    These are X11 and GLUT programs: raw Xlib calls have no Wayland
    equivalent, and GLUT's support for it is poor enough that a window either
    does not appear or does not answer.  Under a compositor the run wants
    ``xvfb-run``, which is what the Linux CI job does -- and what a developer
    on such a session should do, since these otherwise go unrun until CI.
    """
    usable = _x_display_is_usable()
    if usable is False or (usable is None and WAYLAND):
        return 'GLUT and raw X11 have no usable Wayland path; run under xvfb-run'
    if usable:
        return None
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


def _angle():
    """An ANGLE this machine can load, which is never a given.

    ANGLE is not installed system-wide anywhere: it travels inside browsers and
    Electron applications, so a machine may hold several copies of different
    ages and no two alike. ``PYOPENGL_ANGLE_PATH`` names the one to use, and
    without it there is nothing to test against.
    """
    from OpenGL.platform.angle import ANGLE_PATH

    directory = os.environ.get(ANGLE_PATH)
    if not directory:
        return ('no ANGLE named; set %s to a directory holding libEGL.dll '
                'and libGLESv2.dll' % (ANGLE_PATH,))
    if not os.path.isfile(os.path.join(directory, 'libEGL.dll')):
        return '%s names %r, which holds no libEGL.dll' % (ANGLE_PATH, directory)
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
    'angle': (_angle, ()),
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
    # child_environment puts the suite on the child's path, so a script can
    # import checkutils and the fixtures by bare name.
    env = child_environment()
    if backends.is_headless(backends.requested(env)):
        env.pop('TEST_WINDOWING', None)
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
