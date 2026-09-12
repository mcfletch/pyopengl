#! /usr/bin/env python3
"""What a built wheel actually carries, beyond the ``.py`` files.

Three kinds of file in this package are not Python and reach an installation
only because the packaging says so: the bundled Windows GLUT and GLE builds
under ``OpenGL/DLLS``, the declaration tables the pure-Python path reads, and
the typing stubs. Each is declared in a different place -- the DLLs by
``MANIFEST.in`` plus setuptools' ``include-package-data``, the rest by
``[tool.setuptools.package-data]`` -- and nothing before this asked the built
artifact whether they arrived.

#127 is a Windows user with no ``OpenGL/DLLS`` directory in their
installation, answered on the ticket with "the DLLS folder is missing, copy
one in yourself". Whatever produced that install, a wheel from this checkout
carries them, and these cases are what keeps that true while
`plans/BUNDLED-DLLS.md <../../plans/BUNDLED-DLLS.md>`_ is still a proposal --
that plan takes the DLLs out into a package of their own, and the case below
is the one it inverts.

https://github.com/mcfletch/pyopengl/issues/127
https://github.com/mcfletch/pyopengl/issues/76
https://github.com/mcfletch/pyopengl/issues/125
"""

import os
import subprocess
import sys
import zipfile

import paths
import pytest


@pytest.fixture(scope='module')
def wheel(tmp_path_factory):
    """The wheel this checkout produces, as a list of member names.

    Built once for the module.  ``--no-build-isolation`` because the point is
    what *this* tree produces with the tools already here, and a fresh build
    environment would be several minutes rather than a couple of seconds.
    """
    into = tmp_path_factory.mktemp('wheel')
    completed = subprocess.run(
        [sys.executable, '-m', 'pip', 'wheel', '--no-deps',
         '--no-build-isolation', '--wheel-dir', str(into), '.'],
        cwd=paths.ROOT, capture_output=True, text=True, timeout=600,
    )
    if completed.returncode != 0:
        pytest.skip('this checkout does not build a wheel here: %s'
                    % (completed.stderr[-2000:],))
    built = list(into.glob('*.whl'))
    assert len(built) == 1, built
    with zipfile.ZipFile(built[0]) as handle:
        return sorted(handle.namelist())


def under(members, directory):
    """The members of ``members`` inside ``directory``, by base name."""
    prefix = directory + '/'
    return sorted(os.path.basename(name) for name in members
                  if name.startswith(prefix) and not name.endswith('/'))


class TestTheBundledWindowsLibraries:
    """``OpenGL/DLLS`` is a directory inside a package with no ``__init__``.

    That is what makes it worth a case: ``packages.find`` does not see it as a
    package, so it arrives only as package data.  It is named in
    ``MANIFEST.in`` and not in ``[tool.setuptools.package-data]``, which works
    because ``include-package-data`` defaults to true for a project configured
    through ``pyproject.toml`` -- a default, in another project's tool, that
    every Windows GLUT user depends on.
    """

    def test_the_freeglut_builds_are_there(self, wheel):
        shipped = [name for name in under(wheel, 'OpenGL/DLLS')
                   if name.startswith('freeglut')
                   and name.endswith('.dll')]
        assert shipped, (
            'no freeglut DLLs in the wheel; OpenGL.GLUT will find nothing on '
            'a Windows machine that has no GLUT of its own'
        )

    def test_the_gle_builds_are_there(self, wheel):
        shipped = [name for name in under(wheel, 'OpenGL/DLLS')
                   if name.startswith('gle') and name.endswith('.dll')]
        assert shipped, 'no GLE DLLs in the wheel'

    def test_the_build_the_current_interpreter_would_ask_for_is_there(
        self, wheel
    ):
        """The platform module asks for one exact name, built from the word
        size and the compiler generation; a wheel carrying five of the six is
        a wheel that fails on one interpreter and nowhere else."""
        shipped = under(wheel, 'OpenGL/DLLS')
        for size in ('32', '64'):
            for vc in ('vc9', 'vc10', 'vc14'):
                assert 'freeglut%s.%s.dll' % (size, vc) in shipped

    def test_the_licences_travel_with_the_binaries(self, wheel):
        """freeglut and GLE are somebody else's code; redistributing a binary
        without its licence is not a thing we may do."""
        shipped = under(wheel, 'OpenGL/DLLS')
        assert 'freeglut_COPYING.txt' in shipped
        assert 'gle_COPYING' in shipped

    def test_every_tracked_file_arrives(self, wheel):
        """Whatever is in the directory in the checkout is what a user gets;
        a file added there and not shipped is the failure #127 describes."""
        tracked = subprocess.run(
            ['git', 'ls-files', 'OpenGL/DLLS'],
            cwd=paths.ROOT, capture_output=True, text=True,
        )
        if tracked.returncode != 0:                # pragma: no cover - no git
            pytest.skip('not a git checkout')
        wanted = sorted(os.path.basename(line)
                        for line in tracked.stdout.split('\n') if line.strip())
        assert wanted, 'no DLLS files tracked in this checkout'
        assert under(wheel, 'OpenGL/DLLS') == wanted


class TestTheDataThePurePythonPathReads:
    def test_the_declaration_tables_are_there(self, wheel):
        """An installation without a compiled extension reads these to build
        its entry points; without them there is no binding at all."""
        assert [name for name in under(wheel, 'OpenGL/raw/_declarations')
                if name.endswith('.dat')]

    def test_py_typed_is_there(self, wheel):
        """Without it a checker ignores every stub beside it."""
        assert 'OpenGL/py.typed' in wheel

    def test_the_stubs_are_there(self, wheel):
        assert [name for name in wheel if name.endswith('.pyi')]
