"""The suite collects, and its sweeps pass, on a platform that has no EGL library.

EGL ships with the graphics driver, and macOS has none at all -- so
``import OpenGL.EGL`` there raises ``ImportError`` naming the missing library.
A module that reaches for it while being imported turns that into a *collection*
error, and pytest abandons the whole run rather than the one module: three such
modules cost the macOS job every root-level test it had, before one of them ran.

Two things make it easy to get wrong, and both are worth stating:

* ``pytest.importorskip('OpenGL.EGL')`` does not skip.  Since pytest 8.2 it
  catches ``ModuleNotFoundError`` alone, and a missing *library* behind a module
  that imports perfectly well is an ``ImportError`` -- so it needs
  ``exc_type=ImportError`` to mean what it reads as.
* An import of a test helper can reach EGL without naming it: ``glcontext_egl``
  is the headless EGL backend, and importing it is importing EGL.

So the check is what the platform would do rather than a rule about imports: a
child that answers every ``OpenGL.raw.EGL`` import the way a machine with no
library does, collecting the same suite -- and running the cases that reach
every API by construction, which have to leave EGL out there rather than fail
on it.
"""

import importlib.util
import os
import subprocess
import sys

import paths
import pytest

from childenv import run_in_child

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT

#: A windowed backend to run the child on, since the headless one it would
#: otherwise choose is EGL's -- and a machine with no EGL library is not running
#: the EGL backend.  ``TEST_WINDOWING=egl`` in this process says what *this*
#: machine renders on and must not follow the child, which is pretending to be
#: a different machine.
def windowed_backend():
    for name, module in (('glfw', 'glfw'), ('pygame', 'pygame')):
        if importlib.util.find_spec(module) is not None:
            return name
    return None

WITHOUT_EGL = r'''
import sys


class NoEGLLibrary:
    """A platform where the EGL binding has no library to bind to."""

    def find_spec(self, name, path=None, target=None):
        if name == 'OpenGL.raw.EGL' or name.startswith('OpenGL.raw.EGL.'):
            raise ImportError(
                'PyOpenGL found no EGL library to bind to on this platform.'
            )
        return None


sys.meta_path.insert(0, NoEGLLibrary())

import pytest

sys.exit(pytest.main(%r))
'''


def without_egl(arguments):
    """Run pytest with `arguments` on a machine with no EGL; answer what it said."""
    backend = windowed_backend()
    if backend is None:
        pytest.skip('no windowed backend installed to collect the GL suites on')
    # conftest sets PYOPENGL_PLATFORM for the egl backend, and it names the
    # interface the entry points load through -- which is the one being taken
    # away, so the child is given none.
    return run_in_child(
        WITHOUT_EGL % (list(arguments),), check=False,
        TEST_WINDOWING=backend, PYOPENGL_PLATFORM=None,
    )


def collect(target):
    """Collect `target` on a machine with no EGL; answer what pytest said."""
    return without_egl(['-q', '--collect-only', target])


def test_the_root_suite_collects():
    completed = collect('tests/')
    assert completed.returncode == 0, (
        'collection failed with no EGL library present:\n%s'
        % (completed.stdout[-3000:] + completed.stderr[-2000:],)
    )


def test_the_gl_suite_collects():
    completed = collect('tests/gl')
    assert completed.returncode == 0, (
        'collection failed with no EGL library present:\n%s'
        % (completed.stdout[-3000:] + completed.stderr[-2000:],)
    )


def test_the_sweeps_over_every_api_pass():
    """Past collecting: the cases that reach every API by construction.

    They walk every declaration in the tables and every module the package
    ships, EGL's among them, so on a machine with no EGL library they have to
    leave EGL out and say so rather than fail on it -- and macOS and Windows
    are both such machines.
    """
    completed = without_egl([
        '-q', '-p', 'no:cacheprovider',
        'tests/bindings/generated/test_every_declaration_resolves.py',
        'tests/bindings/generated/test_every_generated_module_imports.py',
    ])
    assert completed.returncode == 0, (
        'the sweeps failed with no EGL library present:\n%s'
        % (completed.stdout[-3000:] + completed.stderr[-2000:],)
    )
