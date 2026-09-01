#! /usr/bin/env python3
"""Choosing an implementation, and what happens when the C one is absent.

A source install without a compiler ships no extension, and asking for the C
implementation there must fall back rather than fail.  These run in
subprocesses because only one implementation can be installed per process.
"""

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REPORT = r'''
import sys

if %(block)r:
    class Absent:
        """Stand in for a build that produced no extension."""

        def find_module(self, name, path=None):
            return None

        def find_spec(self, name, target=None, path=None):
            if name in ('OpenGL_accelerate.dispatch', 'OpenGL._dispatch._dispatch'):
                raise ImportError('no extension in this build')
            return None

    sys.meta_path.insert(0, Absent())

import OpenGL.GL as GL
import OpenGL._dispatch as dispatch

print(
    '%%s %%s %%s' %% (dispatch.AVAILABLE, dispatch.ACTIVE, type(GL.glBindTexture).__name__)
)
'''


def report(dispatch, block=False):
    environment = dict(os.environ)
    environment['PYOPENGL_DISPATCH'] = dispatch
    environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    completed = subprocess.run(
        [sys.executable, '-c', REPORT % {'block': block}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    available, active, kind = completed.stdout.strip().split()
    return available == 'True', active == 'True', kind


def _default():
    environment = dict(os.environ)
    environment.pop('PYOPENGL_DISPATCH', None)
    environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    completed = subprocess.run(
        [sys.executable, '-c', REPORT % {'block': False}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    available, active, kind = completed.stdout.strip().split()
    return available == 'True', active == 'True', kind


def test_the_c_implementation_is_the_default():
    """From 4.0 it is what a caller gets without asking."""
    available, active, kind = _default()
    if not available:
        pytest.skip('the C dispatch extension is not built')
    assert active
    assert kind == 'GLProc'


def test_the_default_falls_back_where_nothing_was_built():
    """A source install without a compiler still runs, on ctypes.

    The default is safe to leave alone precisely because of this: asking for
    the C implementation where there is no extension is not an error.
    """
    available, active, kind = report('c', block=True)
    assert not available
    assert not active
    assert kind != 'GLProc'


def test_asking_for_c_selects_it():
    available, active, kind = report('c')
    if not available:
        pytest.skip('the C dispatch extension is not built')
    assert active
    assert kind == 'GLProc'


def test_asking_for_c_without_an_extension_falls_back():
    """A source install with no compiler still runs, on ctypes."""
    available, active, kind = report('c', block=True)
    assert not available
    assert not active
    assert kind != 'GLProc'


def test_asking_for_ctypes_selects_it_even_when_c_is_available():
    _available, active, kind = report('ctypes')
    assert not active
    assert kind != 'GLProc'
