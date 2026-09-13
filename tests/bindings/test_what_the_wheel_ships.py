#! /usr/bin/env python3
"""What a built wheel actually carries, beyond the ``.py`` files.

Two kinds of file in this package are not Python and reach an installation
only because ``[tool.setuptools.package-data]`` says so: the declaration
tables the pure-Python path reads, and the typing stubs. Nothing but the built
artifact can say whether they arrived.

The third kind used to be the Windows freeglut and GLE builds, and the cases
here are the ones that kept them arriving. They ship as
``PyOpenGL-glut-binaries`` now -- ``pip install PyOpenGL[glut]`` -- so what
these cases hold is the opposite: that the wheel carries no binaries at all.
A ``.dll`` reappearing in it is a Linux or macOS install downloading Windows
libraries it cannot load, which is the whole of what the split was for, and
it would come back silently.

See `plans/BUNDLED-DLLS.md <../../plans/BUNDLED-DLLS.md>`_.

https://github.com/mcfletch/pyopengl/issues/164
https://github.com/mcfletch/pyopengl/issues/127
https://github.com/mcfletch/pyopengl/issues/76
https://github.com/mcfletch/pyopengl/issues/125
"""

import os
import subprocess
import sys
import tomllib
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


class TestTheWheelCarriesNoWindowsBinaries:
    """The freeglut and GLE builds are ``PyOpenGL-glut-binaries`` now.

    This wheel is ``py3-none-any``, so anything in it is downloaded by every
    platform. Six freeglut builds and six GLE builds reaching a Linux server
    rendering through EGL is what the split ended, and #164 is a scanner
    quarantining PyOpenGL itself over two of them -- for users who never
    wanted GLUT.

    Nothing would announce their return. They arrived through ``MANIFEST.in``
    and setuptools' ``include-package-data``, which is a default in another
    project's tool: one line restored, or a directory of binaries added
    anywhere under the package, and every install carries them again.
    """

    def test_no_dll_is_in_the_wheel_at_all(self, wheel):
        shipped = [name for name in wheel if name.lower().endswith('.dll')]
        assert not shipped, (
            'Windows binaries are back in the pure-Python wheel, so every '
            'Linux and macOS install now downloads them: %s' % (shipped,)
        )

    def test_the_bundled_directory_is_gone(self, wheel):
        assert not under(wheel, 'OpenGL/DLLS')

    def test_the_checkout_does_not_carry_them_either(self):
        """The sdist ships what is tracked, and a checkout is what a developer
        builds from -- so the files being absent from the wheel while still in
        the tree would only mean they were not being *shipped* yet."""
        tracked = subprocess.run(
            ['git', 'ls-files', 'OpenGL/DLLS'],
            cwd=paths.ROOT, capture_output=True, text=True,
        )
        if tracked.returncode != 0:                # pragma: no cover - no git
            pytest.skip('not a git checkout')
        assert not tracked.stdout.strip(), tracked.stdout

    def test_the_extra_that_replaces_them_is_declared(self):
        """A user told to run ``pip install PyOpenGL[glut]`` has to get
        something: an undeclared extra installs nothing and says nothing."""
        with open(os.path.join(paths.ROOT, 'pyproject.toml'), 'rb') as source:
            declared = tomllib.load(source)
        extras = declared['project']['optional-dependencies']
        assert 'glut' in extras, sorted(extras)
        assert any('glut-binaries' in requirement.lower()
                   for requirement in extras['glut']), extras['glut']


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
