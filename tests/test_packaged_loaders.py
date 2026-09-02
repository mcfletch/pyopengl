"""``OpenGL.raw`` has to resolve under loaders that are not the filesystem.

The modules under :mod:`OpenGL.raw` are built from the shipped declaration
tables rather than imported from files, so whatever reads those tables decides
whether the library works at all.  Reading them with :func:`open` on a path
built from ``__file__`` works only where the package is a directory: inside a
zip -- the ``pex`` / ``shiv`` / ``zipapp`` / Lambda-layer shape -- and inside a
frozen application, that path names nothing, and the failure surfaces several
frames later as an ``ImportError`` for a module that ought to exist.

Both cases are a subprocess and an assertion that the thing starts.
"""

import os
import subprocess
import sys
import zipfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGE = os.path.join(ROOT, 'OpenGL')

#: Enough to prove the tables were read: a raw module that is synthesised, a
#: name it declares, and the friendly import that reaches for it first.
PROGRAM = """
import OpenGL
from OpenGL.raw.GL.VERSION.GL_1_1 import glBegin, GL_TRIANGLES
import OpenGL.GL
print('ok', OpenGL.__version__, hex(int(GL_TRIANGLES)), glBegin is not None)
"""


def _environment(**pinned):
    environment = dict(os.environ)
    environment.setdefault('PYOPENGL_PLATFORM', 'glx')
    # The compiled dispatch cannot be imported out of a zip, and this is about
    # the tables rather than about which implementation reads them.
    environment['PYOPENGL_DISPATCH'] = 'ctypes'
    environment.update(pinned)
    return environment


@pytest.fixture(scope='module')
def archive(tmp_path_factory):
    """The package zipped up, as ``pex``/``shiv``/``zipapp`` would ship it."""
    path = tmp_path_factory.mktemp('zipimport') / 'pyopengl.zip'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as handle:
        for directory, folders, files in os.walk(PACKAGE):
            folders[:] = [f for f in folders if f != '__pycache__']
            for name in files:
                if name.endswith(('.pyc', '.pyo')):
                    continue
                full = os.path.join(directory, name)
                handle.write(full, os.path.relpath(full, ROOT))
    return str(path)


@pytest.fixture(scope='module')
def frozen(tmp_path_factory):
    """A three-line application frozen through the hook PyOpenGL ships."""
    pytest.importorskip('PyInstaller')
    work = tmp_path_factory.mktemp('freeze')
    script = work / 'application.py'
    script.write_text(PROGRAM, encoding='utf-8')
    completed = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', '--onedir', '--noconfirm',
         '--distpath', str(work / 'dist'), '--workpath', str(work / 'build'),
         '--specpath', str(work), str(script)],
        # From the checkout, so that the analysis resolves OpenGL to this tree
        # rather than depending on how the interpreter was installed.
        capture_output=True, text=True, timeout=1800, env=_environment(), cwd=ROOT,
    )
    assert completed.returncode == 0, (
        'PyInstaller could not build a three-line application:\n%s'
        % (completed.stderr[-4000:],))
    return work / 'dist' / 'application' / 'application'


class TestImportingFromAZip:
    """The package zipped up and put on ``sys.path``."""

    def test_the_tables_are_read_from_the_archive(self, archive):
        # cwd anywhere but ROOT, so the directory beside the zip cannot answer.
        completed = subprocess.run(
            [sys.executable, '-c', PROGRAM],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.dirname(archive),
            env=_environment(PYTHONPATH=archive),
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.startswith('ok '), completed.stdout

    def test_it_really_came_from_the_archive(self, archive):
        """Otherwise the test above passes on an installed copy."""
        completed = subprocess.run(
            [sys.executable, '-c', 'import OpenGL; print(OpenGL.__file__)'],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.dirname(archive),
            env=_environment(PYTHONPATH=archive),
        )
        assert completed.returncode == 0, completed.stderr
        assert archive in completed.stdout, completed.stdout


class TestFreezingAnApplication:
    """PyInstaller, through the hook PyOpenGL ships for itself."""

    def test_the_frozen_application_starts(self, frozen):
        completed = subprocess.run(
            [str(frozen)], capture_output=True, text=True, timeout=300,
            env=_environment(),
        )
        assert completed.returncode == 0, (
            'the frozen application failed:\n%s\n%s'
            % (completed.stdout, completed.stderr))
        assert completed.stdout.startswith('ok '), completed.stdout

    def test_the_tables_were_collected(self, frozen):
        """The hook's job, named so that losing it fails here rather than there."""
        root = frozen.parent
        tables = list(root.rglob('_declarations/*.dat'))
        assert tables, 'no declaration tables in %s' % (root,)
