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

import importlib.util
import os
import sys

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
