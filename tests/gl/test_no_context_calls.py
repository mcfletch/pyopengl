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

import backends
from childenv import run_in_child
from glcontext import CHILD_PREAMBLE, NOTHING_TO_TEST_WITH

#: Backends that cannot be put in the situation these cases are about: a
#: context torn down with the dispatch layer never told.  Both of them are
#: PyOpenGL's own context implementations, and both say something on the way
#: out, so ``release(forget=False)`` does not buy the silence the case needs.
#:
#: ``wgl`` -- destroying a pbuffer needs a context current to resolve
#: ``wglDestroyPbufferARB`` through, and it cannot be the one being destroyed,
#: so ``OpenGL.WGL.offscreen`` borrows its bootstrap context and names it.  The
#: compiled layer follows whichever context it last dispatched in, so what a
#: call meets afterwards is that context's table rather than the dead one's.
#:
#: ``tk`` -- ``OpenGL.Tk`` owns its widget's context and retires the table in
#: ``WGLContext.destroy``, for the same reason ``OpenGL.WGL.offscreen`` does:
#: a caller reaching for the widget directly has no fixture to do it for them.
#: It also makes and destroys two throwaway contexts per widget, whose handles
#: the driver hands out again.
#:
#: The parity these cases defend is asked of every backend that *can* be made
#: silent -- glfw, pygame, and the headless egl and cgl ones.
_TELLS_THE_LAYER_REGARDLESS = ('wgl', 'tk')

tells_the_layer_regardless = pytest.mark.skipif(
    backends.requested() in _TELLS_THE_LAYER_REGARDLESS,
    reason='this backend owns its context and says when it goes, so the call '
           'under test does not meet a context the layer was never told about',
)

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
# Resolve glDeleteProgram while a context is still current. Everything above
# GL 1.1 comes from wglGetProcAddress on Windows, and that needs one -- so an
# entry point first *reached* after the context has gone fails at the lookup,
# which is a step earlier than the behaviour under test.
glDeleteProgram(glCreateProgram())
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


def behaviour(dispatch, checking, debug_output=True):
    completed = run_in_child(
        SCRIPT % {'checking': checking},
        check=False,
        PYOPENGL_DISPATCH=dispatch, PYOPENGL_USE_ACCELERATE=None,
        PYOPENGL_ERROR_DEBUG_OUTPUT=('1' if debug_output else '0'),
    )
    if completed.returncode == NOTHING_TO_TEST_WITH:
        pytest.skip('no GL context to lose here: %s' % (completed.stderr.strip(),))
    if completed.returncode != 0:
        pytest.skip('could not run under %s: %s' % (dispatch, completed.stderr[-400:]))
    return completed.stdout.strip().splitlines()[-1]


@tells_the_layer_regardless
@pytest.mark.parametrize('debug_output', [True, False],
                         ids=['debug-output', 'get-error'])
def test_the_default_is_quiet_under_both_implementations(debug_output):
    """The flag is off by default, so the call is a no-op, as it is today.

    **The parity is what this defends**: the C implementation must not diverge
    from ctypes, under either error-checking mechanism.

    What "no-op" comes out as is not PyOpenGL's to decide, and it varies. On the
    ``glGetError`` round trip it is the platform's answer: ``libGL`` answers
    zero with no context current, so the call is silent, while ``opengl32``
    reports GL_INVALID_OPERATION and the checker turns that into a GLError --
    the shutdown-time exception a Windows application meets. Through
    GL_KHR_debug there is no round trip to answer: the check reads a flag the
    driver's callback sets, no callback runs where there is no context to run
    it, and the call is silent everywhere.
    """
    ctypes_says = behaviour('ctypes', False, debug_output)
    assert behaviour('c', False, debug_output) == ctypes_says
    windows_round_trip = sys.platform == 'win32' and not debug_output
    assert ctypes_says == ('other:GLError' if windows_round_trip else 'quiet')


@pytest.mark.parametrize('debug_output', [True, False],
                         ids=['debug-output', 'get-error'])
def test_context_checking_raises_under_both_implementations(debug_output):
    """With the flag on, both say what went wrong -- it is asked before the
    call, so neither mechanism is reached."""
    assert behaviour('ctypes', True, debug_output) == 'raised'
    assert behaviour('c', True, debug_output) == 'raised'


if __name__ == '__main__':
    unittest.main()
