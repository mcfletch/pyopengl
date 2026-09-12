#! /usr/bin/env python3
"""The package imports with error checking switched off.

``PYOPENGL_ERROR_CHECKING=0`` is a documented configuration flag and the one a
program reaches for when it has finished debugging: a ``glGetError`` round
trip per call is the single largest cost PyOpenGL adds, and a renderer making
tens of thousands of calls a frame turns it off.

Switching it off makes ``OpenGL.error._ErrorChecker`` ``None`` -- there is no
checker, which is the point -- so every module that builds one has to expect
that.  A module that does not raises

    TypeError: 'NoneType' object is not callable

from its first line, which is an import that fails rather than a call that
does, and says nothing about the flag responsible.  The reporter of #166 was
looking at that traceback with no way to tell what was missing, and asked for
exactly this: that the library say what is wrong rather than fail in a way
only its author can read.

Asked in a child per namespace, because the flag is read when the entry points
are built and that happens once per process.

https://github.com/mcfletch/pyopengl/issues/166
"""

import pytest

import platforms
from childenv import run_in_child

#: Every API namespace a user imports.  EGL is included only where the
#: platform can bind it: it raises ImportError naming the library where the
#: machine has none, which is a different answer and its own case elsewhere.
NAMESPACES = ('GL', 'GLU', 'GLUT', 'GLES1', 'GLES2', 'GLES3', 'GLSC2', 'GLX',
              'EGL', 'WGL')


def importable(namespace):
    return platforms.bindable(namespace)


@pytest.mark.parametrize('namespace', NAMESPACES)
def test_the_namespace_imports_with_checking_off(namespace):
    if not importable(namespace):
        pytest.skip('the %s platform cannot bind %s'
                    % (platforms.selected() or 'default', namespace))
    completed = run_in_child(
        'import OpenGL.%s' % (namespace,),
        check=False,
        PYOPENGL_ERROR_CHECKING='0',
    )
    assert completed.returncode == 0, (
        'import OpenGL.%s fails with PYOPENGL_ERROR_CHECKING=0:\n%s'
        % (namespace, completed.stderr[-1500:]))


@pytest.mark.parametrize('namespace', NAMESPACES)
def test_the_namespace_has_no_checker_with_checking_off(namespace):
    """Not merely that it imports: that it imported to the right state.

    A module that caught the TypeError and carried on with some other object
    in place would import and then check errors nobody asked it to check.
    """
    if not importable(namespace):
        pytest.skip('the %s platform cannot bind %s'
                    % (platforms.selected() or 'default', namespace))
    completed = run_in_child(
        'import OpenGL.raw.%s._errors as errors\n'
        'print(errors._error_checker is None)' % (namespace,),
        check=False,
        PYOPENGL_ERROR_CHECKING='0',
    )
    if completed.returncode != 0:
        pytest.fail('OpenGL.raw.%s._errors will not import with checking '
                    'off:\n%s' % (namespace, completed.stderr[-1500:]))
    assert completed.stdout.strip().splitlines()[-1] == 'True', (
        'with checking off %s still built a checker' % (namespace,))


def test_checking_on_is_still_the_default():
    """The flag is the exception; a run that sets nothing gets a checker."""
    completed = run_in_child(
        'import OpenGL.raw.GL._errors as errors\n'
        'print(errors._error_checker is not None)',
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-1500:]
    assert completed.stdout.strip().splitlines()[-1] == 'True'
