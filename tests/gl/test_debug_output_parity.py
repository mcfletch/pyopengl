#! /usr/bin/env python3
"""GL_KHR_debug reporting is a cheaper *notice*, not a different policy.

``use_debug_output`` promises that what a caller sees does not change: the same
exception, raised from the same call.  Two things have to hold for that to be
true -- an entry point the caller switched checking off for stays unchecked, and
the exception carries a GL error code where ``GLError`` documents one.

Run in subprocesses because ``OpenGL.ERROR_CHECKING`` is read once, when
``OpenGL._configflags`` is first imported, and one process can only answer for
one setting.
"""

import os
import subprocess
import sys

import paths
import pytest

from childenv import run_in_child
from glcontext import CHILD_PREAMBLE, NOTHING_TO_TEST_WITH

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT

PROGRAM = CHILD_PREAMBLE + r'''
import OpenGL
OpenGL.ERROR_CHECKING = %(checking)r

context = context_or_exit(debug_context=True)

import OpenGL.GL as GL
from OpenGL import error, _dispatch

if not _dispatch.ACTIVE:
    raise SystemExit(NOTHING_TO_TEST_WITH)
GL.glGetString(GL.GL_VERSION)
if not _dispatch.use_debug_output():
    raise SystemExit(NOTHING_TO_TEST_WITH)
%(scope)s

try:
    GL.glEnable(0xDEAD)
except error.GLError as raised:
    print('raised', hex(int(raised.err)))
else:
    print('silent')
'''


def run(checking, scope=''):
    # The children here are parametrised over the dispatch implementation, so
    # an ambient PYOPENGL_USE_ACCELERATE would decide for them.
    completed = run_in_child(
        PROGRAM % {'checking': checking, 'scope': scope},
        check=False,
        PYOPENGL_USE_ACCELERATE=None,
    )
    if completed.returncode == NOTHING_TO_TEST_WITH:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout.strip()


class TestDebugOutputHonoursTheCallersPolicy:
    def test_it_does_not_switch_error_checking_back_on(self):
        """A program that turned checking off for the speed asked for silence,
        and turning debug reporting on is not it asking to be told."""
        assert run(checking=False) == 'silent'

    def test_it_does_not_override_a_per_entry_point_setting(self):
        assert (
            run(
                checking=True,
                scope='_dispatch.set_error_checking(False, GL.glEnable)',
            )
            == 'silent'
        )

    def test_it_still_reports_where_checking_is_on(self):
        assert run(checking=True).startswith('raised')


class TestDebugOutputReportsAGLErrorCode:
    def test_err_is_the_gl_error_and_not_a_driver_message_id(self):
        """``GLError.err`` is documented as the GL error constant, and
        ``error.py`` formats it as one.  A driver's own message identifier in
        that field is a number a caller cannot branch on."""
        assert run(checking=True) == 'raised %s' % (hex(0x0500),)  # GL_INVALID_ENUM


RAISER_DECLINES = CHILD_PREAMBLE + r'''
import OpenGL
OpenGL.ERROR_CHECKING = True

context = context_or_exit(debug_context=True)

import OpenGL.GL as GL
from OpenGL import _dispatch
from OpenGL._dispatch import support

if not _dispatch.ACTIVE:
    raise SystemExit(NOTHING_TO_TEST_WITH)
GL.glGetString(GL.GL_VERSION)
# A context offering GL_KHR_debug is given it without asking, so the
# glGetError half of this comparison has to say it wants the other one.
if not _dispatch.use_debug_output(%(debug)r):
    raise SystemExit(NOTHING_TO_TEST_WITH)

# A client that replaced the raiser with one that returns instead of raising.
support.%(raiser)s = lambda *args, **named: None

try:
    GL.glEnable(0xDEAD)
except SystemError as raised:
    print('SystemError', raised)
except Exception as raised:
    print(type(raised).__name__, str(raised).splitlines()[0])
else:
    print('silent')
'''


@pytest.mark.parametrize(
    'debug,raiser',
    [(False, 'raise_gl_error'), (True, 'raise_debug_error')],
    ids=['glGetError', 'GL_KHR_debug'],
)
def test_a_raiser_that_declines_does_not_become_a_SystemError(debug, raiser):
    """Both notice mechanisms return -1 to say "an exception is set".  A raiser
    that returns instead leaves the stub returning NULL with nothing raised,
    which CPython reports as a SystemError from an unrelated frame."""
    completed = run_in_child(RAISER_DECLINES % {'debug': debug, 'raiser': raiser}, check=False, PYOPENGL_USE_ACCELERATE=None)
    if completed.returncode == NOTHING_TO_TEST_WITH:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    answer = completed.stdout.strip()
    assert not answer.startswith('SystemError'), answer
    assert answer.startswith('NullFunctionError'), answer


DISABLE = CHILD_PREAMBLE + r'''
context = context_or_exit(debug_context=True)

import OpenGL.GL as GL
from OpenGL import _dispatch, dispatch

if not _dispatch.ACTIVE:
    raise SystemExit(NOTHING_TO_TEST_WITH)
GL.glGetString(GL.GL_VERSION)

for _ in range(4):
    if not dispatch.use_debug_output():
        raise SystemExit(NOTHING_TO_TEST_WITH)
held_after_enabling = len(dispatch._installed_callbacks)
dispatch.use_debug_output(False)
print(
    held_after_enabling,
    len(dispatch._installed_callbacks),
    bool(GL.glIsEnabled(0x92E0)),          # GL_DEBUG_OUTPUT
    bool(GL.glIsEnabled(0x8242)),          # GL_DEBUG_OUTPUT_SYNCHRONOUS
)
'''


def test_turning_debug_output_off_undoes_what_turning_it_on_did():
    """The synchronous debug output it enables serialises the driver, so
    leaving it on costs exactly what switching the mode off asked to stop
    paying -- and each enable must not add another callback to hold forever."""
    completed = run_in_child(DISABLE, check=False, PYOPENGL_USE_ACCELERATE=None)
    if completed.returncode == NOTHING_TO_TEST_WITH:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    held, left, output, synchronous = completed.stdout.split()
    assert held == '1', 'four enables held %s callbacks' % (held,)
    assert left == '0'
    assert output == 'False'
    assert synchronous == 'False'
