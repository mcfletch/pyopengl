#! /usr/bin/env python3
"""An installation that cannot say what it is says so.

A directory named ``OpenGL`` with no ``__init__.py`` in it, on ``sys.path``,
is imported as a namespace package.  The finder that does that runs ahead of
the one an editable install adds, so an empty directory wins over the real
installation -- and the submodules still load, because the editable install's
finder answers for those by name.  The result is a package whose own module
never ran, holding none of the configuration flags, with every submodule
present and correct.  What that looks like is an ``ImportError`` from
``OpenGL._configflags``, four frames inside a friendly module's import.

Two ordinary things leave such a directory: an install that replaced a wheel
with an editable install of the same project and left the emptied directory
behind, and a directory of that name in whatever directory a script was run
from.

Only an installation reached through a finder can be shadowed this way.  A
namespace portion is used when *nothing* on ``sys.path`` is a package, so a
copy in site-packages answers first and there is nothing to shadow -- and the
cases here say so rather than passing for that reason.
"""

import os
import subprocess
import sys

import pytest

import paths


def run(where, source):
    """`source` in a child run from ``where``, which is its ``sys.path[0]``."""
    return subprocess.run(
        [sys.executable, '-c', source],
        capture_output=True, text=True, cwd=where, timeout=300,
    )


@pytest.fixture
def husk(tmp_path):
    """A directory holding nothing but the name, run from.

    Skipped where this installation is not one an empty directory can get in
    front of.
    """
    (tmp_path / 'OpenGL').mkdir()
    where = str(tmp_path)
    settled = run(where, 'import OpenGL; print(getattr(OpenGL, "__file__", None))')
    if settled.returncode == 0 and settled.stdout.strip() not in ('None', ''):
        pytest.skip(
            'this installation answers from sys.path (%s), so nothing shadows it'
            % (settled.stdout.strip(),)
        )
    return where


class TestTheFailureNamesItself:
    def test_it_says_what_was_imported_instead(self, husk):
        completed = run(husk, 'from OpenGL.WGL import offscreen')
        assert completed.returncode != 0, completed.stdout
        assert 'namespace package' in completed.stderr, completed.stderr

    def test_and_where_the_directory_is(self, husk):
        """The one thing a reader has to have: somewhere to go and look.

        The directory is empty, so nothing else in the failure points at it.
        """
        completed = run(husk, 'import OpenGL._configflags')
        assert os.path.join(husk, 'OpenGL') in completed.stderr, completed.stderr

    def test_a_sound_installation_is_untouched(self, tmp_path):
        """The guard costs an ordinary import nothing but the question."""
        completed = run(
            str(tmp_path),
            'import OpenGL._configflags as c; print(c.ERROR_CHECKING)',
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() in ('True', 'False'), completed.stdout


#: ``setup.py`` with the platform it decides by forced, and ``setup`` itself
#: replaced by something that records what it was handed.  Windows because
#: that is the branch that has ever declared ``data_files``, and where the
#: prefix is a site directory -- ``site.getsitepackages()`` there answers
#: ``[prefix, prefix\\Lib\\site-packages]``, so a directory installed into the
#: prefix is a directory on ``sys.path``.
DECLARED = '''
import runpy
import sys

import setuptools

recorded = {}
setuptools.setup = lambda **named: recorded.update(named)
sys.platform = 'win32'
runpy.run_path('setup.py', run_name='__main__')
print(repr(recorded.get('data_files') or []))
'''


class TestNothingIsInstalledOutsideThePackage:
    """``data_files`` with a relative target installs into the *install
    prefix*, not into the package.  Naming one ``OpenGL/DLLS`` puts an
    ``OpenGL`` directory with no ``__init__.py`` in it in the prefix -- which
    on Windows is a directory the interpreter imports from, so it shadows the
    real package for every process that runs from anywhere but the checkout.

    Nothing reads the copy: ``ctypesloader.DLL_DIRECTORY`` is
    ``os.path.dirname(OpenGL.__file__)/DLLS``, inside the package, which is
    where the DLLs ship as package data.
    """

    def test_the_build_declares_no_data_files(self):
        completed = subprocess.run(
            [sys.executable, '-c', DECLARED],
            capture_output=True, text=True, cwd=paths.ROOT, timeout=300,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == '[]', (
            'setup.py declares data_files, which install relative to the '
            'prefix rather than into the package: %s' % (completed.stdout.strip(),)
        )

    def test_the_windows_dlls_ship_inside_the_package(self):
        """Which is what makes the declaration above unnecessary as well as
        harmful: they are already where the loader looks."""
        from OpenGL.platform import ctypesloader

        assert os.path.isdir(ctypesloader.DLL_DIRECTORY), \
            ctypesloader.DLL_DIRECTORY
        assert any(
            name.endswith('.dll')
            for name in os.listdir(ctypesloader.DLL_DIRECTORY)
        ), os.listdir(ctypesloader.DLL_DIRECTORY)
