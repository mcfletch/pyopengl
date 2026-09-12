#! /usr/bin/env python3
"""The C Cython writes is only good for the toolchain that wrote it.

``accelerate/src/*.c`` is generated from the ``.pyx`` beside it and is not
tracked, so it accumulates in a checkout and is reused by every later build.
Those modules ``cimport numpy``, which is to say the generated C is written
against numpy's own declarations -- and ``cythonize`` decides whether to write
it again by comparing timestamps. A wheel-installed numpy carries the
timestamps recorded in the wheel, which can be older than a ``.c`` generated
from a previous numpy last week; the stale C is then compiled against headers
that no longer match it, and the compiler reports an error inside a numpy
internal, naming nothing in this package.

``accelerate/setup.py`` records which Cython and numpy wrote the C, and drops
it where either has moved.
"""

import importlib.metadata
import importlib.util
import os
import shutil
import sys
import sysconfig

import paths
import pytest


def accelerate_setup():
    """accelerate's setup.py, imported for what it declares."""
    root = os.path.join(paths.ROOT, 'accelerate')
    if not os.path.exists(os.path.join(root, 'setup.py')):
        pytest.skip('the accelerate source tree is not in this checkout')
    sys.path.insert(0, root)
    try:
        import setup as accelerate_setup
    except ImportError as err:              # pragma: no cover - no source tree
        pytest.skip('accelerate/setup.py is not importable here: %s' % (err,))
    finally:
        sys.path.pop(0)
    return accelerate_setup


#: Cython is what writes the C, so where it is absent there is nothing to
#: write it again with and the shipped C is all there is -- which is a case of
#: its own, covered below rather than skipped.
needs_cython = pytest.mark.skipif(
    importlib.util.find_spec('Cython') is None,
    reason='Cython writes the generated C; there is none to write here')


class TestTheToolchainIsRecorded:
    @needs_cython
    def test_it_names_the_cython_that_writes_the_c(self):
        from Cython import __version__ as cython_version

        assert cython_version in accelerate_setup()._toolchain()

    @needs_cython
    def test_it_names_the_numpy_the_c_is_written_against(self):
        """Or says there is none: an environment without numpy builds every
        module but the numpy format handler, and the C is written for that."""
        stated = accelerate_setup()._toolchain()
        if importlib.util.find_spec('numpy') is None:
            assert 'numpy none' in stated
        else:
            import numpy

            assert numpy.__version__ in stated

    def test_the_drop_happens_only_when_the_file_is_run(self):
        """Reading what a setup file declares is not a build.

        The suite and the packaging tools both import it for its declarations,
        and this test module is one of them -- so a drop at module level would
        cost every run of the suite a re-cythonise of ten modules, and would do
        it while another build was compiling them. Read from the source rather
        than by importing it, because importing it is the thing being ruled
        out.
        """
        import ast

        path = os.path.join(paths.ROOT, 'accelerate', 'setup.py')
        if not os.path.exists(path):        # pragma: no cover - no source tree
            pytest.skip('the accelerate source tree is not in this checkout')
        with open(path, encoding='utf-8') as handle:
            tree = ast.parse(handle.read())

        def calls(node):
            return [found for found in ast.walk(node)
                    if isinstance(found, ast.Call)
                    and isinstance(found.func, ast.Name)
                    and found.func.id == 'drop_c_from_another_toolchain']

        guarded = [call for statement in tree.body
                   if isinstance(statement, ast.If)
                   for call in calls(statement)]
        assert calls(tree) == guarded, (
            'it is called outside the `__name__ == "__main__"` guard, so '
            'importing this file deletes generated C')
        assert guarded, 'nothing calls it, so a stale .c is still compiled'


class TestWhatIsDroppedAndWhatIsKept:
    """Driven against a directory of this test's own: the checkout's own
    generated C is what a build is about to compile."""

    @pytest.fixture
    def elsewhere(self, tmp_path, monkeypatch):
        setup = accelerate_setup()
        source = tmp_path / 'src'
        source.mkdir()
        (source / 'wrapper.c').write_text('/* generated */\n')
        (source / 'wrapper.pyx').write_text('# the source\n')
        monkeypatch.setattr(setup, 'HERE', str(tmp_path))
        monkeypatch.setattr(setup, 'TOOLCHAIN_STAMP',
                            str(source / '.cython-toolchain'))
        return setup, source

    @needs_cython
    def test_c_from_another_toolchain_is_dropped(self, elsewhere):
        setup, source = elsewhere
        monkeypatched = setup
        monkeypatched.drop_c_from_another_toolchain()
        assert not (source / 'wrapper.c').exists()
        assert (source / 'wrapper.pyx').exists(), (
            'the source it would be written from must be left alone')

    @needs_cython
    def test_the_toolchain_is_recorded_as_it_goes(self, elsewhere):
        setup, source = elsewhere
        setup.drop_c_from_another_toolchain()
        assert (source / '.cython-toolchain').read_text() == setup._toolchain()

    @needs_cython
    def test_a_second_build_keeps_the_c(self, elsewhere):
        """Regenerating on every build would cost a minute for nothing."""
        setup, source = elsewhere
        setup.drop_c_from_another_toolchain()
        (source / 'wrapper.c').write_text('/* generated again */\n')
        setup.drop_c_from_another_toolchain()
        assert (source / 'wrapper.c').exists()

    @needs_cython
    def test_a_moved_toolchain_drops_it_again(self, elsewhere):
        setup, source = elsewhere
        setup.drop_c_from_another_toolchain()
        (source / 'wrapper.c').write_text('/* generated again */\n')
        (source / '.cython-toolchain').write_text('cython 0.29\nnumpy 1.26\n')
        setup.drop_c_from_another_toolchain()
        assert not (source / 'wrapper.c').exists()

    def test_without_cython_the_shipped_c_is_kept(self, elsewhere, monkeypatch):
        """An install from an sdist with no Cython has the C and no way to
        make more of it."""
        setup, source = elsewhere
        monkeypatch.setattr(setup, 'have_cython', False)
        setup.drop_c_from_another_toolchain()
        assert (source / 'wrapper.c').exists()


class TestTheSourcesCompileWithTheCythonInstalled:
    """Every ``.pyx`` in the accelerator turns into C with the Cython here.

    An sdist install runs Cython over these sources on the user's machine,
    against whatever Cython their environment resolved.  So a construct Cython
    stops accepting is not a warning on the way to a working build -- it is
    every source install of ``PyOpenGL_accelerate`` failing on that Cython
    onwards, on every platform at once, and the wheels not covering it.

    Cython 3.1 dropping ``long`` as a builtin name is the case that happened:
    ``vbo.pyx`` used it, and the release then would not build anywhere Cython
    had reached 3.1 -- reported from Raspberry Pi, from arm64 and from an Intel
    Mac within a month of each other, each read as an architecture problem
    because that is what the reporter had in front of them.

    https://github.com/mcfletch/pyopengl/issues/147
    https://github.com/mcfletch/pyopengl/issues/145
    https://github.com/mcfletch/pyopengl/issues/79
    """

    def sources(self):
        root = os.path.join(paths.ROOT, 'accelerate', 'src')
        if not os.path.isdir(root):
            pytest.skip('the accelerate source tree is not in this checkout')
        found = sorted(
            name for name in os.listdir(root) if name.endswith('.pyx')
        )
        assert found, root
        return root, found

    @needs_cython
    @pytest.mark.slow
    def test_every_pyx_cythonizes(self, tmp_path):
        """Through the command line, which is the interface a build uses.

        Cython's Python API has moved between the releases this has to run
        under; ``python -m cython`` has not. One file per call, so a failure
        names the file it is in rather than the first of nine.
        """
        import subprocess

        root, found = self.sources()
        failed = []
        for name in found:
            completed = subprocess.run(
                [sys.executable, '-m', 'cython', '-3',
                 '-I', root, '-I', os.path.join(paths.ROOT, 'accelerate'),
                 os.path.join(root, name),
                 '-o', str(tmp_path / (name[:-4] + '.c'))],
                capture_output=True, text=True, timeout=300,
            )
            if completed.returncode:
                failed.append(f'--- {name} ---\n{completed.stderr.strip()}')
        assert not failed, (
            'Cython %s refuses these sources:\n%s'
            % (importlib.metadata.version('cython'), '\n\n'.join(failed))
        )


#: The diagnostics that have stopped a build of this package, promoted back to
#: errors so a test says so before a user's compiler does.  Both are about a
#: pointer where a scalar belongs or the reverse, which is the class of mistake
#: generated C makes when the API it was generated against has moved.
FATAL_DIAGNOSTICS = ('-Werror=int-conversion',
                     '-Werror=incompatible-pointer-types')


class TestTheGeneratedCSatisfiesClangToo:
    """The other compiler reads the generated C without complaint.

    gcc compiles this package on every Linux build, so its opinion is the one
    always heard.  clang's is the one that arrives as a bug report: it is the
    system compiler on macOS and the BSDs, and it has twice turned a
    diagnostic gcc still permits into an error -- ``-Wint-conversion`` at
    clang 15, ``-Wincompatible-pointer-types`` after it.  Each time, every
    source install of ``PyOpenGL_accelerate`` on those platforms stopped
    working while every Linux build stayed green.

    Syntax-only, so this costs about a second for the whole set: what is being
    asked is whether the compiler accepts the code, not whether the object
    file it would emit is any good.  The build itself is what produces those.

    https://github.com/mcfletch/pyopengl/issues/107
    https://github.com/mcfletch/pyopengl/issues/117
    """

    def clang(self):
        found = shutil.which('clang')
        if found is None:
            pytest.skip('no clang here; gcc is exercised by every build')
        return found

    def generated(self):
        root = os.path.join(paths.ROOT, 'accelerate', 'src')
        if not os.path.isdir(root):
            pytest.skip('the accelerate source tree is not in this checkout')
        found = sorted(name for name in os.listdir(root) if name.endswith('.c'))
        if not found:
            pytest.skip(
                'no generated C to read -- this is an environment with the '
                'accelerator not built, and there is nothing yet to compile')
        return root, found

    def includes(self, root):
        paths_ = ['-I' + root, '-I' + os.path.join(paths.ROOT, 'accelerate'),
                  '-I' + sysconfig.get_paths()['include']]
        try:
            import numpy
        except ImportError:
            return paths_
        return paths_ + ['-I' + numpy.get_include(),
                         '-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION']

    def test_clang_accepts_every_generated_module(self):
        import subprocess

        clang = self.clang()
        root, found = self.generated()
        includes = self.includes(root)
        refused = []
        for name in found:
            completed = subprocess.run(
                [clang, '-fsyntax-only', *FATAL_DIAGNOSTICS, *includes,
                 os.path.join(root, name)],
                capture_output=True, text=True, timeout=300,
            )
            if completed.returncode:
                errors = [line for line in completed.stderr.splitlines()
                          if 'error:' in line]
                refused.append('--- %s ---\n%s' % (name, '\n'.join(errors[:6])))
        assert not refused, 'clang refuses:\n' + '\n\n'.join(refused)


@pytest.fixture(scope='module')
def archive(tmp_path_factory):
    """The sdist this checkout produces, as a list of member names.

    Built once for the module: it is a couple of seconds, and four cases ask
    the same question of it.
    """
    import subprocess
    import tarfile

    root = os.path.join(paths.ROOT, 'accelerate')
    if not os.path.exists(os.path.join(root, 'setup.py')):
        pytest.skip('the accelerate source tree is not in this checkout')
    into = tmp_path_factory.mktemp('sdist')
    completed = subprocess.run(
        [sys.executable, 'setup.py', 'sdist', '--dist-dir', str(into), '-q'],
        cwd=root, capture_output=True, text=True, timeout=600,
    )
    assert completed.returncode == 0, completed.stderr[-3000:]
    built = list(into.glob('*.tar.gz'))
    assert len(built) == 1, built
    with tarfile.open(built[0]) as handle:
        # Drop the leading `name-version/` that sdists wrap everything in.
        return sorted(name.split('/', 1)[1]
                      for name in handle.getnames() if '/' in name)


class TestWhatTheSdistShips:
    """The source release carries sources, and the C it cannot regenerate.

    Two kinds of generated C live under ``accelerate/src`` and they are not
    the same question.

    ``src/*.c`` is Cython's output from the ``.pyx`` beside it.  Cython is a
    hard build requirement of this package, so every install from an sdist has
    one and writes that C itself -- and ``drop_c_from_another_toolchain``
    deletes any that came in the archive, because the sdist carries no
    toolchain stamp for it to match against.  Shipping it is therefore weight
    that is deleted on arrival, and weight with a hazard attached: it is
    exactly the stale C that fails to compile against a numpy it was not
    written for, which is what the ticket reports of other projects.

    ``src/c/**/*.c`` is the dispatch layer, generated from the Khronos
    registry by a tool that does *not* run at install time and is not shipped.
    That C has to be in the archive or the package cannot be built at all.

    https://github.com/mcfletch/pyopengl/issues/121
    https://github.com/mcfletch/pyopengl/issues/12
    """

    @pytest.mark.slow
    def test_every_pyx_is_shipped(self, archive):
        """Without these there is nothing to build from at all."""
        shipped = [name for name in archive if name.endswith('.pyx')]
        assert len(shipped) >= 9, shipped

    @pytest.mark.slow
    def test_the_pxd_files_are_shipped(self, archive):
        """#12: without them a `cimport` in a .pyx has nothing to read, and
        regenerating the C from an sdist fails on the first module."""
        shipped = [name for name in archive if name.endswith('.pxd')]
        assert shipped, 'no .pxd files in the sdist'
        assert 'OpenGL_accelerate/__init__.py' in archive, (
            'the package directory has no __init__.py, so the .pxd files in '
            'it are not a package Cython can cimport from')

    @pytest.mark.slow
    def test_no_cython_output_is_shipped(self, archive):
        """#121: one `.c` per `.pyx`, and every one of them a liability."""
        cython_output = {
            name[:-4] + '.c' for name in archive
            if name.startswith('src/') and name.endswith('.pyx')
        }
        shipped = sorted(cython_output & set(archive))
        assert not shipped, (
            '%d Cython-generated file(s) in the sdist; every install deletes '
            'and rewrites them, and a stale one is a compile error inside a '
            'numpy header naming nothing in this package:\n  %s'
            % (len(shipped), '\n  '.join(shipped)))

    @pytest.mark.slow
    def test_the_dispatch_layer_c_is_shipped(self, archive):
        """The other kind, which nothing at install time can write again."""
        shipped = [name for name in archive
                   if name.startswith('src/c/') and name.endswith('.c')]
        assert shipped, (
            'the registry-generated dispatch C is missing, and the generator '
            'that writes it does not run at install time')
