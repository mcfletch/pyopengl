"""What importing ``OpenGL.EGL`` does where there is no EGL library.

An EGL implementation is not present everywhere PyOpenGL runs: a headless CI
runner installs no graphics driver, and the Windows and macOS platforms load no
EGL at all.  The bindings have nothing to call without one, so the import
fails -- and the way it fails is what callers work from, because ``try: from
OpenGL import EGL`` is how a program asks whether this machine has EGL.

Each case runs in a subprocess: the question is what happens the *first* time
the module is imported, and this process has already answered it.
"""

import os
import subprocess
import sys

import paths
import pytest

from childenv import run_in_child

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT

#: Each of these reaches for the library directly, so each has to answer for
#: itself: ``OpenGL.EGL`` is the friendly package, ``_types`` holds the
#: declarations under it, and ``_errors`` builds an error checker around
#: ``eglGetError`` -- and an extension module imports that one without the
#: others.
IMPORT_EGL = r'''
import importlib

for name in ('OpenGL.EGL', 'OpenGL.raw.EGL._types', 'OpenGL.raw.EGL._errors'):
    try:
        importlib.import_module(name)
    except ImportError as err:
        print(err)
    else:
        raise SystemExit('%s imported where there is no EGL library' % (name,))
'''

#: The loader looked for libEGL and found none -- a machine with no graphics
#: driver installed.
NO_LIBRARY = '''
import OpenGL.platform as platform
platform.PLATFORM.EGL = None
''' + IMPORT_EGL

#: The platform has no EGL interface to offer at all, as win32 and darwin do
#: not, so the attribute is not merely empty but absent.
NO_INTERFACE = '''
import OpenGL.platform as platform
kind = type(platform.PLATFORM)
if 'EGL' in vars(kind):
    delattr(kind, 'EGL')
vars(platform.PLATFORM).pop('EGL', None)
''' + IMPORT_EGL


def run(source):
    """Run `source` in a fresh interpreter and return what it printed."""
    completed = run_in_child(source)
    assert completed.returncode == 0, completed.stderr[-2000:] or completed.stdout
    return completed.stdout


@pytest.mark.parametrize('source', [NO_LIBRARY, NO_INTERFACE],
                         ids=['no-library', 'no-interface'])
class TestWithoutAnEGLImplementation:
    def test_the_import_raises_import_error(self, source):
        """Anything else is uncatchable by the caller who asked the question."""
        run(source)

    def test_the_message_says_what_is_missing(self, source):
        message = run(source)
        assert 'EGL' in message
        assert 'PyOpenGL' in message, 'says who could not load it'
