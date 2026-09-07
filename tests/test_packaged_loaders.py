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

from childenv import child_environment

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
    environment = child_environment()
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


class TestTheHookDeclaresWhatIsReachedByName:
    """A module a string names is a module a freezer cannot see.

    The Tk GL widget makes its context through the window system's own API and
    chooses which implementation to use at run time, from the windowing system
    Tk turns out to be running on -- so an application frozen without them
    builds cleanly, opens its window and fails on the context.
    """

    def _hook(self):
        """``hiddenimports`` as PyInstaller would read them"""
        pytest.importorskip('PyInstaller')
        completed = subprocess.run(
            [sys.executable, '-c',
             'import runpy, json, os;'
             'declared = runpy.run_path(os.path.join('
             '%r, "OpenGL", "__pyinstaller", "hook-OpenGL.py"));'
             'print(json.dumps(declared["hiddenimports"]))' % (ROOT,)],
            capture_output=True, text=True, timeout=600, cwd=ROOT,
            env=_environment(),
        )
        assert completed.returncode == 0, completed.stderr
        import json

        return json.loads(completed.stdout.splitlines()[-1])

    def test_every_tk_context_implementation_is_carried(self):
        from OpenGL.Tk import context

        pytest.importorskip('tkinter')
        declared = self._hook()
        for module, _ in context.IMPLEMENTATIONS.values():
            assert module in declared, (
                '%s is chosen by name at run time and would not be frozen'
                % (module,))

    def test_every_apis_error_checker_is_carried(self):
        """Every binding `_declarations` builds imports `OpenGL.raw.<api>._errors`
        by name, so an API whose checker was left out fails on the first call
        into it -- and only GL's and EGL's are imported anywhere statically."""
        declared = self._hook()
        for api in ('GL', 'GLU', 'GLX', 'EGL', 'WGL', 'GLES2'):
            module = 'OpenGL.raw.%s._errors' % (api,)
            assert module in declared, (
                '%s is imported by name and would not be frozen' % (module,))

    def test_the_platform_modules_are_still_carried(self):
        """The registries this has always reported; named so that adding the
        above cannot quietly replace them."""
        assert 'OpenGL.platform.linux' in self._hook()


class TestADamagedTableSaysSo:
    """The declaration tables are the only description of ``OpenGL.raw`` there
    is, so one that cannot be read is a broken installation.  What a user must
    not get is ``ValueError: bad marshal data`` from inside an import of
    ``OpenGL.GL``, several frames from the file that is wrong."""

    @pytest.fixture
    def read_table(self):
        from OpenGL import _declarations

        _declarations.clear_caches()
        yield _declarations._read_table
        _declarations.clear_caches()

    @pytest.mark.parametrize(
        'blob',
        [
            pytest.param(b'', id='empty'),
            pytest.param(b'\xe3\x00', id='truncated'),
            pytest.param(b'not marshalled data at all', id='wrong-format'),
        ],
    )
    def test_a_corrupt_table_raises_ImportError_naming_the_file(
        self, read_table, blob, tmp_path, monkeypatch
    ):
        from OpenGL import _declarations

        damaged = tmp_path / 'GL.dat'
        damaged.write_bytes(blob)
        monkeypatch.setattr(_declarations, '_table', lambda name: damaged)
        with pytest.raises(ImportError) as caught:
            read_table('GL.dat')
        assert 'GL.dat' in str(caught.value)
        assert 'declaration table' in str(caught.value)

    def test_a_missing_table_still_raises_ImportError(
        self, read_table, tmp_path, monkeypatch
    ):
        from OpenGL import _declarations

        monkeypatch.setattr(
            _declarations, '_table', lambda name: tmp_path / 'absent.dat'
        )
        with pytest.raises(ImportError):
            read_table('GL.dat')
