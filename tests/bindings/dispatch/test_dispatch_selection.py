#! /usr/bin/env python3
"""Choosing an implementation, and what happens when the C one is absent.

A source install without a compiler ships no extension, and asking for the C
implementation there must fall back rather than fail.  These run in
subprocesses because only one implementation can be installed per process.
"""

import os
import subprocess
import sys

import paths
import pytest
from childenv import child_environment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT

REPORT = r'''
import sys

if %(block)r:
    class Absent:
        """Stand in for a build that produced no extension."""

        def find_module(self, name, path=None):
            return None

        def find_spec(self, name, target=None, path=None):
            if name in ('OpenGL_accelerate.dispatch', 'OpenGL._dispatch._dispatch'):
                raise ImportError('no extension in this build')
            return None

    sys.meta_path.insert(0, Absent())

import OpenGL.GL as GL
import OpenGL._dispatch as dispatch

print(
    '%%s %%s %%s' %% (dispatch.AVAILABLE, dispatch.ACTIVE, type(GL.glBindTexture).__name__)
)
'''


def report(dispatch, block=False):
    environment = child_environment(PYOPENGL_DISPATCH=dispatch)
    completed = subprocess.run(
        [sys.executable, '-c', REPORT % {'block': block}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    available, active, kind = completed.stdout.strip().split()
    return available == 'True', active == 'True', kind


def _default():
    environment = child_environment()
    environment.pop('PYOPENGL_DISPATCH', None)
    completed = subprocess.run(
        [sys.executable, '-c', REPORT % {'block': False}],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    available, active, kind = completed.stdout.strip().split()
    return available == 'True', active == 'True', kind


def test_the_c_implementation_is_the_default():
    """From 4.0 it is what a caller gets without asking."""
    available, active, kind = _default()
    if not available:
        pytest.skip('the C dispatch extension is not built')
    assert active
    assert kind == 'GLProc'


def test_the_default_falls_back_where_nothing_was_built():
    """A source install without a compiler still runs, on ctypes.

    The default is safe to leave alone precisely because of this: asking for
    the C implementation where there is no extension is not an error.
    """
    available, active, kind = report('c', block=True)
    assert not available
    assert not active
    assert kind != 'GLProc'


def test_asking_for_c_selects_it():
    available, active, kind = report('c')
    if not available:
        pytest.skip('the C dispatch extension is not built')
    assert active
    assert kind == 'GLProc'


def test_asking_for_c_without_an_extension_falls_back():
    """A source install with no compiler still runs, on ctypes."""
    available, active, kind = report('c', block=True)
    assert not available
    assert not active
    assert kind != 'GLProc'


def test_asking_for_ctypes_selects_it_even_when_c_is_available():
    _available, active, kind = report('ctypes')
    assert not active
    assert kind != 'GLProc'


class TestVersionPairing:
    """The two packages share the generated slot numbering and table layout, so
    a mismatched pair does not fail cleanly -- it dispatches through the wrong
    indices.  The check that stops that has to be able to fail."""

    def test_the_extension_states_the_version_it_was_generated_with(self):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')
        from OpenGL.version import __version__

        assert dispatch._c.__pyopengl_version__ == __version__

    def test_an_extension_that_will_not_say_is_a_mismatch(self, monkeypatch):
        """An older accelerate is exactly the pair this exists to refuse, and
        an older accelerate is what would not carry the attribute -- so
        'it did not say' must not read as 'it agrees'."""
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')

        class Silent:
            pass

        monkeypatch.setattr(dispatch, '_c', Silent())
        assert not dispatch._versions_match()

    def test_a_different_version_is_a_mismatch(self, monkeypatch):
        dispatch = pytest.importorskip('OpenGL._dispatch')
        if not dispatch.AVAILABLE:
            pytest.skip('the C dispatch extension is not built')

        class Older:
            __pyopengl_version__ = '3.1.9'

        monkeypatch.setattr(dispatch, '_c', Older())
        assert not dispatch._versions_match()


MISMATCH = r'''
import OpenGL
from OpenGL import _dispatch


class Older:
    """An accelerate from a different release, which is what the guard exists for."""

    __pyopengl_version__ = '3.1.9'


if not _dispatch.AVAILABLE:
    print('UNBUILT')
else:
    _dispatch._c = Older()
    try:
        print('RETURNED', _dispatch.install())
    except ImportError as error:
        print('RAISED', error)
'''


def _mismatched(**environment_overrides):
    """Ask a fresh interpreter to install a deliberately mismatched extension."""
    environment = child_environment()
    environment.pop('PYOPENGL_DISPATCH', None)
    environment.pop('PYOPENGL_USE_ACCELERATE', None)
    environment.update(environment_overrides)
    completed = subprocess.run(
        [sys.executable, '-c', MISMATCH],
        capture_output=True, text=True, cwd=ROOT, env=environment, timeout=300,
        check=False,        # the child's own report is what this reads
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    answer = completed.stdout.strip()
    if answer == 'UNBUILT':
        pytest.skip('the C dispatch extension is not built')
    return answer


class TestTheSwitchIsReadWhenItIsAsked:
    """``OpenGL.USE_ACCELERATE = False`` is the documented way to run on ctypes,
    and it is what the version-mismatch error tells a caller to reach for. A
    program sets it in the lines after ``import OpenGL``, so it has to be read
    then and not at whatever moment ``_configflags`` first happened to load --
    a framework, a profiler or another binding stacked on PyOpenGL may have
    imported that already, and the switch would silently do nothing."""

    def _active(self, preamble=''):
        script = (
            '%simport OpenGL\n'
            'OpenGL.USE_ACCELERATE = False\n'
            'import OpenGL.GL\n'
            'import OpenGL._dispatch as dispatch\n'
            'print("ACTIVE", dispatch.ACTIVE)\n' % (preamble,)
        )
        completed = subprocess.run(
            [sys.executable, '-c', script], capture_output=True, text=True,
            check=False)
        line = [x for x in completed.stdout.splitlines()
                if x.startswith('ACTIVE')]
        assert line, completed
        return line[0].split()[1]

    def test_setting_it_runs_on_ctypes(self):
        assert self._active() == 'False'

    def test_and_still_does_where_something_read_the_flags_first(self):
        """The import that freezes the snapshot need not be the caller's."""
        assert self._active('import OpenGL._configflags\n') == 'False'

    @pytest.mark.parametrize('preamble', ['', 'import OpenGL._configflags\n'])
    def test_the_cython_accelerators_answer_to_it_too(self, preamble):
        """The same switch turns off the wrapper, array-datatype and
        format-handler accelerators, which decide at their own import."""
        script = (
            '%simport OpenGL\n'
            'OpenGL.USE_ACCELERATE = False\n'
            'import OpenGL.GL\n'
            'from OpenGL import acceleratesupport\n'
            'print("AVAILABLE", acceleratesupport.ACCELERATE_AVAILABLE)\n'
            % (preamble,)
        )
        completed = subprocess.run(
            [sys.executable, '-c', script], capture_output=True, text=True,
            check=False)
        line = [x for x in completed.stdout.splitlines()
                if x.startswith('AVAILABLE')]
        assert line, completed
        assert line[0].split()[1] == 'False'


class TestThePairIsPinnedBeforeItIsInstalled:
    """The runtime check refuses a mismatched pair; the metadata stops one
    being assembled. Both are wanted: an ImportError at the first entry point
    is a worse place to learn this than the resolver."""

    def test_accelerate_requires_pyopengl_at_its_own_version(self):
        """They are released together and share generated tables, so the
        version that pairs with this accelerate is this accelerate's own."""
        import re

        root = paths.ROOT
        setup = os.path.join(root, 'accelerate', 'setup.py')
        if not os.path.exists(setup):
            pytest.skip('the accelerate source tree is not in this checkout')
        with open(setup, encoding='utf-8') as handle:
            source = handle.read()
        assert re.search(r'install_requires\s*=', source), (
            'accelerate declares no dependency on PyOpenGL, so pip will '
            'assemble any pair of versions it is asked for')

    def test_the_declared_pin_is_the_version_it_was_built_from(self):
        sys.path.insert(0, os.path.join(
            paths.ROOT, 'accelerate'))
        try:
            import setup as accelerate_setup
        except ImportError as err:              # pragma: no cover - no source tree
            # ImportError alone, and with the reason: a bare `except Exception`
            # here turned anything at all -- including a warning the run had
            # asked to be an error -- into a skip that named the source tree.
            pytest.skip('accelerate/setup.py is not importable here: %s' % (err,))
        finally:
            sys.path.pop(0)
        requirements = accelerate_setup.pyopengl_requirement()
        assert requirements == 'PyOpenGL==%s' % (accelerate_setup._our_version(),)


class TestTheFloorForTheOtherAccelerators:
    """``acceleratesupport`` gates the accelerators that do *not* share the
    generated tables -- the wrapper, the array datatypes, the format handlers.
    They track PyOpenGL's internals all the same, so the floor has to keep up
    with the version that is being released."""

    def test_it_is_not_left_behind_by_a_major_version(self):
        from OpenGL import acceleratesupport
        from OpenGL.version import __version__

        ours = tuple(int(part) for part in __version__.split('.')[:1]
                     if part.isdigit())
        assert acceleratesupport.needed_version[:1] == ours, (
            'the floor names %r while PyOpenGL is %s'
            % (acceleratesupport.needed_version, __version__))

    def test_an_accelerate_from_the_previous_major_is_below_it(self):
        from OpenGL import acceleratesupport

        assert (3, 1, 10) < acceleratesupport.needed_version


class TestAskingForCtypesInstead:
    """USE_ACCELERATE is the switch PyOpenGL has always had for "do not use the
    compiled layer", and somebody whose pair does not match reaches for it to
    get running again.  It has to be honoured before the pair is judged, or the
    answer to "I do not want the extension" is an error about the extension."""

    def test_a_mismatched_pair_is_refused_when_the_extension_is_wanted(self):
        assert _mismatched().startswith('RAISED')

    def test_the_error_names_a_way_out_that_works(self):
        message = _mismatched()
        assert 'PYOPENGL_USE_ACCELERATE' in message or 'PYOPENGL_DISPATCH' in message

    def test_turning_the_flag_off_runs_on_ctypes_rather_than_raising(self):
        assert _mismatched(PYOPENGL_USE_ACCELERATE='0') == 'RETURNED False'

    def test_the_older_dispatch_switch_still_works_too(self):
        assert _mismatched(PYOPENGL_DISPATCH='ctypes') == 'RETURNED False'
