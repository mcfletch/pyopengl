#! /usr/bin/env python3
"""``OpenGL.dispatch``: which implementation is running, and control of it.

The names a program is meant to call live in a module without a leading
underscore, and a program that needs the C implementation can ask whether it
actually got it -- the extension is optional, so asking for it and running
without it is a state a caller may need to fail on.

Most of these run in subprocesses: which implementation is installed is settled
once per process.
"""

import os
import subprocess
import sys

import pytest

from childenv import child_environment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: Stands in for a build that produced no extension, so the fallback can be
#: tested where the extension *is* built.  Mirrors tests/test_dispatch_selection.
BLOCK = '''
import sys


class Absent:
    """Stand in for a build that produced no extension."""

    def find_module(self, name, path=None):
        return None

    def find_spec(self, name, target=None, path=None):
        if name in ('OpenGL_accelerate.dispatch', 'OpenGL._dispatch._dispatch'):
            raise ImportError('no extension in this build')
        return None


sys.meta_path.insert(0, Absent())
'''


def run(source, block=False, **environment_overrides):
    """Run `source` in a fresh interpreter and hand back what it printed."""
    environment = child_environment()
    environment.pop('PYOPENGL_DISPATCH', None)
    environment.pop('PYOPENGL_USE_ACCELERATE', None)
    environment.update(environment_overrides)
    completed = subprocess.run(
        [sys.executable, '-c', (BLOCK if block else '') + source],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout.strip()


def built():
    """Whether this checkout has the compiled layer to test against."""
    from OpenGL import dispatch

    return dispatch.available()


class TestTheModuleIsThePublicOne:
    """The names PyOpenGL's documentation tells a program to call."""

    def test_the_documented_names_are_importable_without_an_underscore(self):
        from OpenGL import dispatch

        for name in (
            'make_current',
            'forget_context',
            'reclaim_retired',
            'set_error_checking',
            'use_debug_output',
            'debug_output_available',
            'requested',
            'active',
            'available',
            'settle',
            'status',
        ):
            assert callable(getattr(dispatch, name)), name

    def test_the_private_module_still_answers_to_the_old_names(self):
        """Code written against the documentation as it stood keeps working."""
        _dispatch = pytest.importorskip('OpenGL._dispatch')
        from OpenGL import dispatch

        for name in ('make_current', 'forget_context', 'set_error_checking'):
            assert getattr(_dispatch, name) is getattr(dispatch, name)


class TestWhatWasAskedForAndWhatIsRunning:
    def test_the_default_is_c_on_cpython(self):
        answer = run(
            'from OpenGL import dispatch; print(dispatch.requested())'
        )
        expected = 'c' if sys.implementation.name == 'cpython' else 'ctypes'
        assert answer == expected

    def test_asking_for_ctypes_is_reported_as_asked_for(self):
        answer = run(
            'from OpenGL import dispatch; print(dispatch.requested())',
            PYOPENGL_DISPATCH='ctypes',
        )
        assert answer == 'ctypes'

    def test_turning_the_accelerators_off_is_a_request_for_ctypes(self):
        answer = run(
            'from OpenGL import dispatch; print(dispatch.requested())',
            PYOPENGL_USE_ACCELERATE='0',
        )
        assert answer == 'ctypes'

    def test_active_reports_the_implementation_the_entry_points_use(self):
        if not built():
            pytest.skip('the C dispatch extension is not built')
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.active(), type(OpenGL.GL.glBindTexture).__name__)'
        )
        assert answer == 'c GLProc'

    def test_active_reports_ctypes_where_ctypes_is_what_runs(self):
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.active())',
            PYOPENGL_DISPATCH='ctypes',
        )
        assert answer == 'ctypes'

    def test_settling_answers_before_an_entry_point_is_built(self):
        """A test harness asks before it has imported the API it will use."""
        if not built():
            pytest.skip('the C dispatch extension is not built')
        answer = run('from OpenGL import dispatch; print(dispatch.settle())')
        assert answer == 'c'


class TestStatusSaysWhyItIsNotWhatWasAskedFor:
    """The extension is optional, so asking for C and getting ctypes is not an
    error -- but a caller who cares has to be able to see it, and to see why."""

    def test_a_build_with_no_extension_says_so(self):
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'state = dispatch.status()\n'
            'print(state.requested, state.active, state.available, state.reason)',
            block=True,
        )
        requested, active, available, reason = answer.split(None, 3)
        assert (requested, active, available) == ('c', 'ctypes', 'False')
        assert 'accelerate' in reason

    def test_the_accelerator_switch_is_named_where_it_is_what_chose_ctypes(self):
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.status().reason)',
            PYOPENGL_USE_ACCELERATE='0',
        )
        assert 'USE_ACCELERATE' in answer

    def test_the_dispatch_switch_is_named_where_it_is_what_chose_ctypes(self):
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.status().reason)',
            PYOPENGL_DISPATCH='ctypes',
        )
        assert 'PYOPENGL_DISPATCH' in answer

    def test_tracing_is_named_where_it_is_what_chose_ctypes(self):
        """FULL_LOGGING selects ctypes, and somebody who did not know that
        needs to be told rather than left wondering where their speed went."""
        answer = run(
            'import OpenGL\n'
            'OpenGL.FULL_LOGGING = True\n'
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.status().reason)',
        )
        assert 'FULL_LOGGING' in answer

    def test_nothing_is_wrong_where_the_c_layer_is_what_runs(self):
        if not built():
            pytest.skip('the C dispatch extension is not built')
        answer = run(
            'import OpenGL.GL\n'
            'from OpenGL import dispatch\n'
            'print(dispatch.status().reason)'
        )
        assert answer == 'None'


class TestAskingCostsNothingOnTheCtypesPath:
    """The extension is 13 MB and nothing else loads it under
    ``PYOPENGL_DISPATCH=ctypes``; a status query must not be what does."""

    def test_the_module_does_not_load_the_extension_to_answer(self):
        answer = run(
            'import sys\n'
            'from OpenGL import dispatch\n'
            'state = dispatch.status()\n'
            'dispatch.make_current(0)\n'
            "print('OpenGL_accelerate.dispatch' in sys.modules, "
            "'OpenGL._dispatch' in sys.modules)",
            PYOPENGL_DISPATCH='ctypes',
        )
        assert answer == 'False False'
