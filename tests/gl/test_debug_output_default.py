#! /usr/bin/env python3
"""A context that offers GL_KHR_debug is checked through it, without asking.

Error checking is on by default, and its whole cost is a ``glGetError`` round
trip after every call.  Where the driver will report an error through a
callback during the call instead, that is the cheaper way to notice the same
error -- so a context that offers it gets it, under either implementation, and
:func:`OpenGL.dispatch.error_checking_mode` says which one a context ended up
with.

In subprocesses because which implementation is installed, and what
``OpenGL.ERROR_DEBUG_OUTPUT`` says, are settled once per process.
"""

import os
import subprocess
import sys

import pytest

from childenv import child_environment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

#: A window with a debug context, or exit 77 to say there is nothing to test
#: with.  Same shape as tests/gl/test_debug_output_parity.py uses.
CONTEXT = '''
import glfw
if not glfw.init():
    raise SystemExit(77)
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
glfw.window_hint(glfw.OPENGL_DEBUG_CONTEXT, glfw.TRUE)
window = glfw.create_window(64, 64, 'debug-default', None, None)
if window is None:
    raise SystemExit(77)
glfw.make_context_current(window)
'''

DEFAULT = '''
%(preamble)s
''' + CONTEXT + '''
import OpenGL.GL as GL
from OpenGL import dispatch, error

GL.glGetString(GL.GL_VERSION)
if not dispatch.debug_output_available():
    raise SystemExit(77)
%(body)s
print(dispatch.error_checking_mode())
try:
    GL.glEnable(0xDEAD)
except error.GLError as raised:
    print('raised', hex(int(raised.err)))
else:
    print('silent')
'''

IMPLEMENTATIONS = ['c', 'ctypes']


def run(implementation, preamble='', body=''):
    """Run the program under one dispatch implementation."""
    environment = child_environment(
        PYOPENGL_DISPATCH=implementation, PYOPENGL_DISPATCH_STRICT='0'
    )
    completed = subprocess.run(
        [sys.executable, '-c', DEFAULT % {'preamble': preamble, 'body': body}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    if completed.returncode == 77:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    mode, raised = completed.stdout.strip().splitlines()
    return mode, raised


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_a_context_offering_it_is_checked_through_it(implementation):
    """Nothing in the program asks: the offer is made when the context is."""
    mode, raised = run(implementation)
    assert mode == 'debug-output'
    assert raised == 'raised 0x500'


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_the_same_error_is_raised_either_way(implementation):
    """The mechanism is how an error is noticed, not which errors there are."""
    mode, raised = run(implementation, body='dispatch.use_debug_output(False)')
    assert mode == 'get-error'
    assert raised == 'raised 0x500'


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_a_program_can_decline_it_before_the_first_call(implementation):
    """For a program that does not want the driver made synchronous."""
    mode, raised = run(
        implementation,
        preamble='import OpenGL\nOpenGL.ERROR_DEBUG_OUTPUT = False',
    )
    assert mode == 'get-error'
    assert raised == 'raised 0x500'


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_turning_it_on_again_is_the_way_back(implementation):
    mode, raised = run(
        implementation,
        body='dispatch.use_debug_output(False)\n'
             'assert dispatch.use_debug_output(True)',
    )
    assert mode == 'debug-output'
    assert raised == 'raised 0x500'


FOREIGN = '''
''' + CONTEXT + '''
import ctypes

import OpenGL.GL as GL
from OpenGL import dispatch, error
from OpenGL.raw.GL._types import GLDEBUGPROC

GL.glGetString(GL.GL_VERSION)
if not dispatch.debug_output_available():
    raise SystemExit(77)

# What an application using GL_KHR_debug for its own diagnostics does.
seen = []
own = GLDEBUGPROC(lambda *arguments: seen.append(arguments[2]))
dispatch.use_debug_output(False)
GL.glEnable(0x92E0)                     # GL_DEBUG_OUTPUT
GL.glDebugMessageCallback(own, None)

print(dispatch.use_debug_output(True))
print(dispatch.error_checking_mode())
try:
    GL.glEnable(0xDEAD)
except error.GLError:
    print('raised')
else:
    print('silent')
'''


DISPLACED = '''
''' + CONTEXT + '''
import OpenGL.GL as GL
from OpenGL import dispatch, error
from OpenGL.raw.GL._types import GLDEBUGPROC

GL.glGetString(GL.GL_VERSION)
if dispatch.error_checking_mode() != 'debug-output':
    raise SystemExit(77)

# An application that installs its own callback *after* PyOpenGL armed the
# context -- or, indistinguishably, a context whose handle was recycled from a
# destroyed one that had been armed.  Either way the flag PyOpenGL reads is
# now a flag nobody sets, and a check that only reads it passes everything.
own = GLDEBUGPROC(lambda *arguments: None)
GL.glDebugMessageCallback(own, None)

GL.glEnable(0xDEAD)                     # an error only the audit can notice
noticed = None
for index in range(dispatch.AUDIT_INTERVAL * 2):
    try:
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
    except error.GLError as raised:
        noticed = (index, int(raised.err))
        break
print(noticed is not None, noticed[1] if noticed else 0, dispatch.error_checking_mode())
'''


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_an_error_is_noticed_even_where_the_callback_is_no_longer_ours(implementation):
    """The flag is only trustworthy while our callback is the one setting it.

    Nothing tells PyOpenGL that a context was destroyed and its handle handed
    out again, or that something replaced the callback, so the check asks the
    driver anyway every AUDIT_INTERVAL calls.  What it finds there puts the
    context back on glGetError, where a check cannot be silently wrong.
    """
    environment = child_environment(
        PYOPENGL_DISPATCH=implementation, PYOPENGL_DISPATCH_STRICT='0'
    )
    completed = subprocess.run(
        [sys.executable, '-c', DISPLACED],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    if completed.returncode == 77:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    noticed, code, mode = completed.stdout.strip().split()
    assert noticed == 'True', 'the error went unnoticed'
    assert code == str(0x0500)
    assert mode == 'get-error', 'the context should have stopped trusting the flag'


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_an_application_callback_is_not_taken_over(implementation):
    """Installing over it would silence the application's own diagnostics, and
    its next glDebugMessageCallback would silence our checking."""
    environment = child_environment(
        PYOPENGL_DISPATCH=implementation, PYOPENGL_DISPATCH_STRICT='0'
    )
    completed = subprocess.run(
        [sys.executable, '-c', FOREIGN],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    if completed.returncode == 77:
        pytest.skip('no GL context offering GL_KHR_debug')
    assert completed.returncode == 0, completed.stderr[-2000:]
    took, mode, raised = completed.stdout.strip().splitlines()
    assert took == 'False'
    assert mode == 'get-error'
    assert raised == 'raised'
