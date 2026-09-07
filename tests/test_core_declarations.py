"""A command that is core is exported as core, not as the extension it came from.

Nearly every GL version adopts extensions wholesale: GL 4.1 is
``ARB_separate_shader_objects`` and five others, GL 4.3 is ``KHR_debug`` and
twenty-one more.  PyOpenGL declares such a command twice, once under the
extension that introduced it and once under the version that adopted it, and
the two declarations differ in one way that matters: **the extension one is
gated on the driver advertising the extension string, and the core one is not.**

A driver is entitled to stop advertising an extension it has promoted, and a
core profile commonly does -- macOS's 4.1 core profile does not list
``GL_ARB_separate_shader_objects``.  Exported under the extension declaration,
``glCreateShaderProgramv`` then raises ``NullFunctionError`` on that driver,
naming a function the context implements.

So the version module's own declaration is the one a client gets.  That is also
what the C dispatch layer does with the same pair -- its table records
``GL_VERSION_GL_4_1`` with the ARB name as an alternate -- which is why this is
asked in a child with the compiled layer switched off: with it installed every
entry point is the C one and already answers correctly, and the question here
is what the ctypes implementation exports.
"""

import json
import os
import subprocess
import sys

import pytest

from childenv import child_environment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Report, as JSON, every command a GL version declares that ``OpenGL.GL``
#: exports under an extension gate.  ``constructFunction`` reads the gate the
#: same way: a name with ``VERSION`` in it is core and stands without a check.
SURVEY = r'''
import json, sys

import OpenGL
OpenGL.USE_ACCELERATE = False          # the ctypes implementation is the subject

from OpenGL import _declarations
import OpenGL.GL as GL

VERSIONS = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 0), (2, 1),
    (3, 0), (3, 1), (3, 2), (3, 3),
    (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
]

core = {}
for major, minor in VERSIONS:
    contents = _declarations.contents_for(
        'OpenGL.raw.GL.VERSION.GL_%d_%d' % (major, minor))
    if contents is None:
        continue
    for command, _arguments, _types in contents['commands']:
        core.setdefault(command, contents['extension'])

gated = {}
for command, version in core.items():
    entry = getattr(GL, command, None)
    if entry is None:
        continue
    base = getattr(entry, 'wrappedOperation', entry)
    extension = getattr(base, 'extension', None)
    if extension and 'VERSION' not in extension.split('_'):
        gated[command] = [version, extension]

arb = getattr(
    __import__('OpenGL.GL.ARB.separate_shader_objects', fromlist=['x']),
    'glCreateShaderProgramv',
)
arb_base = getattr(arb, 'wrappedOperation', arb)

json.dump(
    {
        'declared': len(core),
        'gated': gated,
        'arb_module_extension': getattr(arb_base, 'extension', None),
    },
    sys.stdout,
)
'''


@pytest.fixture(scope='module')
def survey():
    completed = subprocess.run(
        [sys.executable, '-c', SURVEY],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=child_environment(PYOPENGL_DISPATCH='ctypes'),
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


def test_the_premise_that_versions_declare_commands_at_all(survey):
    """A guard on the machinery below: an empty table would pass everything."""
    assert survey['declared'] > 700


def test_no_core_command_is_exported_under_an_extension_gate(survey):
    gated = survey['gated']
    assert gated == {}, sorted(gated.items())[:20]


@pytest.mark.parametrize(
    'command',
    [
        'glCreateShaderProgramv',
        'glDebugMessageCallback',
        'glTexStorage2D',
        'glDispatchCompute',
        'glGetPointerv',
    ],
)
def test_the_ones_a_macos_core_profile_refused(survey, command):
    """Named individually, because each is a call that stopped working."""
    assert command not in survey['gated']


def test_the_extension_module_still_declares_its_own(survey):
    """Taking the core declaration must not empty the extension module: a
    client that imports it by name is asking for the gated one."""
    assert survey['arb_module_extension'] == 'GL_ARB_separate_shader_objects'
