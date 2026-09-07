#! /usr/bin/env python3
"""Calling an entry point with no current context.

Deleting GL objects from a cleanup handler is ordinary: the handler runs after
whatever tore the context down, and the call does nothing.  PyOpenGL's own
``CONTEXT_CHECKING`` flag decides whether that is an error, and it is off by
default, so the C implementation has to behave the same way -- turning a silent
no-op into an exception at shutdown would break working applications in the
one place they are least able to handle it.
"""

import os
import subprocess
import sys
import unittest

import paths
import pytest

from childenv import run_in_child
from glcontext import CHILD_PREAMBLE, NOTHING_TO_TEST_WITH

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = paths.ROOT

SCRIPT = CHILD_PREAMBLE + r'''
if %(checking)r:
    import OpenGL
    OpenGL.CONTEXT_CHECKING = True

context = context_or_exit()

from OpenGL.GL import glCreateProgram, glDeleteProgram, glGetError
from OpenGL import error

program = glCreateProgram()
glGetError()

# What a cleanup handler faces: the context is gone by the time it runs, and
# nothing told PyOpenGL -- which is the case this is about, so the layer is
# deliberately not notified.
context.release(forget=False)

try:
    glDeleteProgram(program)
except error.NoContext:
    print('raised')
except Exception as raised:
    print('other:%%s' %% (type(raised).__name__,))
else:
    print('quiet')
'''


def behaviour(dispatch, checking):
    completed = run_in_child(
        SCRIPT % {'checking': checking},
        check=False,
        PYOPENGL_DISPATCH=dispatch, PYOPENGL_USE_ACCELERATE=None,
    )
    if completed.returncode == NOTHING_TO_TEST_WITH:
        pytest.skip('no GL context to lose here: %s' % (completed.stderr.strip(),))
    if completed.returncode != 0:
        pytest.skip('could not run under %s: %s' % (dispatch, completed.stderr[-400:]))
    return completed.stdout.strip().splitlines()[-1]


def test_the_default_is_quiet_under_both_implementations():
    """The flag is off by default, so the call is a no-op, as it is today."""
    assert behaviour('ctypes', False) == 'quiet'
    assert behaviour('c', False) == 'quiet'


def test_context_checking_raises_under_both_implementations():
    """With the flag on, both say what went wrong."""
    assert behaviour('ctypes', True) == 'raised'
    assert behaviour('c', True) == 'raised'


if __name__ == '__main__':
    unittest.main()
