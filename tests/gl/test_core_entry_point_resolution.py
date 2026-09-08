#! /usr/bin/env python3
"""An entry point the GL library exports resolves, whoever declares it.

A name can be declared twice: ``glGetPointerv`` is GL 1.1 and ``GL_KHR_debug``
re-specifies it, giving it the pnames that report a debug callback.  Which of
the two a caller reaches is settled by which module they import from, and on
Windows that decided whether the entry point worked at all: ``opengl32``
exports GL 1.1 and ``wglGetProcAddress`` answers for everything *above* it,
returning NULL for the 1.1 set, and an extension-declared name was looked for
in the second place only.  Nothing said so -- the name is defined, and only
calling it reports anything.

``OpenGL.GL`` exports the core declaration, so what it holds is resolved as
core; ``OpenGL.GL.KHR.debug`` holds the extension's own, and that one is the
name this rule is still what answers for.  Both are asked here, because the
point is that the choice of module is not a choice about whether the function
exists.

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

#: ``(module, name)`` for an entry point a core version *and* an extension both
#: declare.  The two modules hold different declarations of it, resolved by
#: different routes, and a caller reaches whichever they imported.
DOUBLY_DECLARED = [
    ('OpenGL.GL', 'glGetPointerv'),
    ('OpenGL.GL.KHR.debug', 'glGetPointerv'),
]

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

import importlib

import OpenGL.GL as GL

GL.glGetString(GL.GL_VERSION)

# A driver that does not advertise the extension, for asking what the gate
# does with one on a machine whose driver does.  Apple's GL is such a machine
# for GL_KHR_debug -- it implements no version that has it -- and so is any
# driver predating an extension that re-specified a core entry point.
denied = %(deny)r
if denied:
    from OpenGL import platform
    advertised = platform.PLATFORM.checkExtension
    platform.PLATFORM.checkExtension = (
        lambda extension: False if extension == denied else advertised(extension)
    )

entry = getattr(importlib.import_module(%(module)r), %(name)r)
print(bool(entry))
'''


def defined(module, name, implementation, deny=None):
    """Whether ``<module>.<name>`` resolves under `implementation`.

    ``deny`` names an extension the driver is to report as absent, so that a
    machine which has it can be asked what a machine without it would find.
    """
    completed = subprocess.run(
        [sys.executable, '-c',
         SCRIPT % {'module': module, 'name': name, 'deny': deny}],
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


@pytest.mark.parametrize('module,name', DOUBLY_DECLARED)
@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_it_resolves_under_either_implementation(module, name, implementation):
    assert defined(module, name, implementation) == 'True', (
        '%s.%s is undefined under the %s implementation'
        % (module, name, implementation)
    )


@pytest.mark.parametrize('module,name', DOUBLY_DECLARED)
@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_it_resolves_though_the_extension_is_absent(module, name,
                                                    implementation):
    """The half of the rule a driver advertising ``GL_KHR_debug`` cannot show.

    ``glGetPointerv`` is GL 1.1, and the extension added pnames to it rather
    than adding it, so it is there whether or not the extension is.  Which is
    what Apple's GL is: 4.1 at most, with no version that has ``GL_KHR_debug``
    in it, and where the extension module's declaration used to answer that a
    GL 1.1 entry point did not exist.
    """
    assert defined(module, name, implementation, deny='GL_KHR_debug') == 'True', (
        '%s.%s is undefined under the %s implementation on a driver that does '
        'not advertise GL_KHR_debug' % (module, name, implementation)
    )


#: An entry point only an extension declares, so the library exporting it says
#: nothing about the context.  ``glGenQueries`` is core; this spelling is not.
EXTENSION_ONLY = ('OpenGL.GL.ARB.occlusion_query', 'glGenQueriesARB')


@pytest.mark.parametrize('implementation', IMPLEMENTATIONS)
def test_an_extension_only_name_is_still_refused(implementation):
    """The aside above is for a name a core version declares, and no wider.

    macOS exports every entry point its framework implements whether or not
    the context does, so a rule that answered from the library alone would
    report an unadvertised extension as present there -- which is the question
    the gate exists to answer.
    """
    module, name = EXTENSION_ONLY
    assert defined(module, name, implementation,
                   deny='GL_ARB_occlusion_query') == 'False', (
        '%s.%s resolved on a driver that does not advertise its extension'
        % (module, name)
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
