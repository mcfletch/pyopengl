#! /usr/bin/env python3
"""An entry point the GL library exports resolves, whoever declares it.

A name can be declared twice: ``glGetPointerv`` is GL 1.1 and ``GL_KHR_debug``
re-specifies it, giving it the pnames that report a debug callback.  Which
declaration ``OpenGL.GL`` ends up holding is settled by import order and is not
something a caller can see -- so it must not decide whether the entry point
works.

It did on Windows.  ``wglGetProcAddress`` answers for entry points above GL 1.1
and returns NULL for the ones ``opengl32`` exports itself, which is the whole
of GL 1.1; an extension-declared name is looked up there and nowhere else, so
``OpenGL.GL.glGetPointerv`` was an undefined function while
``OpenGL.GL.VERSION.GL_1_1.glGetPointerv`` beside it worked.  Nothing said so:
the name is defined, and only calling it reports anything.

The parity case runs in subprocesses, because which implementation is installed
is settled once per process and the two resolve entry points by different
routes, which is what is being compared.  The rule underneath it is asked here
in this one.
"""

import ctypes
import os
import subprocess
import sys

import pytest

from childenv import child_environment
from gltestcase import GLTestCase

from OpenGL import platform
from OpenGL.platform.baseplatform import BasePlatform

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

#: Entry points declared by a core version *and* by an extension, so that the
#: two declarations resolve by different routes and only one of them can be the
#: one a caller reaches.
DOUBLY_DECLARED = ['glGetPointerv']

IMPLEMENTATIONS = ['c', 'ctypes']

SCRIPT = '''
import glfw
if not glfw.init():
    raise SystemExit(77)
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
window = glfw.create_window(64, 64, 'resolution', None, None)
if window is None:
    raise SystemExit(77)
glfw.make_context_current(window)

import OpenGL.GL as GL

GL.glGetString(GL.GL_VERSION)
entry = getattr(GL, %(name)r)
print(bool(entry))
'''


def defined(name, implementation):
    """Whether ``OpenGL.GL.<name>`` resolves under `implementation`."""
    completed = subprocess.run(
        [sys.executable, '-c', SCRIPT % {'name': name}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=child_environment(
            PYOPENGL_DISPATCH=implementation, PYOPENGL_DISPATCH_STRICT='0'
        ),
        timeout=300,
    )
    if completed.returncode == 77:
        pytest.skip('no GL context to resolve against')
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout.strip().splitlines()[-1]


@pytest.mark.parametrize('name', DOUBLY_DECLARED)
@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_it_resolves_under_either_implementation(name, implementation):
    assert defined(name, implementation) == 'True', (
        '%s is undefined under the %s implementation' % (name, implementation)
    )


#: An extension no driver advertises, for asking what the gate does with one.
ABSENT = 'GL_NOT_AN_EXTENSION_ANY_DRIVER_HAS'


class TestTheLibraryExportIsNotGatedByAnExtension(GLTestCase):
    """What ``force_base`` means, asked of the rule rather than the platform.

    A driver that does not advertise ``GL_KHR_debug`` still has
    ``glGetPointerv``: it is GL 1.1, and the extension added pnames to it
    rather than adding it.  So the route that says "look in the library" does
    not first ask whether the extension is advertised -- otherwise which driver
    is in front of us would decide whether a GL 1.1 entry point exists.

    ``BasePlatform`` directly, because a platform is free to try every route
    and Windows does: asked through the platform, both cases below resolve and
    neither says which route answered.
    """

    gl_version = (1, 1)

    def _built(self, **named):
        return BasePlatform.constructFunction(
            platform.PLATFORM,
            'glGetPointerv',
            platform.PLATFORM.GL,
            resultType=None,
            argTypes=(ctypes.c_uint, ctypes.c_void_p),
            argNames=('pname', 'params'),
            **named
        )

    def test_the_gate_refuses_an_absent_extension(self):
        """The gate does its job, so the next case is about standing aside."""
        with pytest.raises(AttributeError):
            self._built(extension=ABSENT)

    def test_and_stands_aside_for_the_library_export(self):
        assert self._built(extension=ABSENT, force_base=True) is not None
