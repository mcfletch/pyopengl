"""A GLUT window title is given as a str on every platform.

Windows takes a different route to ``glutCreateWindow``: FreeGLUT there calls
``exit()`` on a fatal error, so the binding goes through
``__glutCreateWindowWithExit`` to register an exit handler instead.  That
override declares its own argument types, and a title type that is not the
portable one makes ``glutCreateWindow('title')`` a ctypes.ArgumentError on
Windows and nowhere else.
"""

import ctypes

import pytest

from OpenGL.raw import GLUT as _raw
import OpenGL.GLUT.special as special


def title_argument_type():
    """The type the title is passed as, by whichever route this platform uses."""
    override = getattr(special, '__glutCreateWindowWithExit', None)
    if override is not None:
        return override.argtypes[0]
    if not _raw.glutCreateWindow:
        pytest.skip('no GLUT library available to declare against')
    return _raw.glutCreateWindow.argtypes[0]


def test_the_title_type_accepts_str():
    """What a caller writes is glutCreateWindow('hello')."""
    title_argument_type().from_param('hello')


def test_the_title_type_accepts_bytes():
    title_argument_type().from_param(b'hello')


def test_the_override_declares_the_portable_title_type():
    """The Windows route and the portable route take the same title."""
    override = getattr(special, '__glutCreateWindowWithExit', None)
    if override is None:
        pytest.skip('this platform does not use the exit-callback override')
    if not _raw.glutCreateWindow:
        pytest.skip('no GLUT library available to declare against')
    assert override.argtypes[0] is _raw.glutCreateWindow.argtypes[0]
