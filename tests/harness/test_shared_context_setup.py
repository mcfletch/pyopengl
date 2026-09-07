"""One mechanism for putting a GL context under a test.

:class:`glcontext.ContextTestCase` with a backend mixin per windowing system is
that mechanism: the suite base cases and the ``testdecorator.gltest`` decorator
are all built on it.

A second mechanism costs more than the duplication: one that names a windowing
library itself cannot render where there is no window, and a headless runner is
what CI has. These hold the suites to the shared fixture, so they keep running
there.
"""

import os
import subprocess
import sys

import backends
import paths
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = paths.ROOT


class TestItRunsWhereThereIsNoWindow:
    """The point of the unification: a headless runner is what CI has."""

    def _run(self, windowing):
        environment = dict(os.environ)
        environment['TEST_WINDOWING'] = windowing
        environment['TEST_VISIBLE'] = '0'
        return subprocess.run(
            [sys.executable, '-m', 'pytest', '-q', '--no-header', '-p',
             'no:randomly', os.path.join('tests', 'gl')],
            cwd=ROOT, env=environment, capture_output=True, text=True,
            check=False)

    @pytest.mark.parametrize('windowing', ['egl'])
    def test_the_gl_suite_is_not_skipped_wholesale(self, windowing):
        completed = self._run(windowing)
        assert 'unavailable under the headless' not in completed.stdout, (
            'tests/gl still skips under %s: %s'
            % (windowing, completed.stdout[-2000:]))

    def test_and_it_actually_passes_there(self):
        completed = self._run('egl')
        if 'no usable GL' in completed.stdout or 'no EGL' in completed.stdout:
            pytest.skip('no headless GL on this machine')
        assert ' passed' in completed.stdout, completed.stdout[-2000:]
        assert 'failed' not in completed.stdout, completed.stdout[-2000:]


class TestNoBackendIsImplementedTwice:
    """A windowing system is wired up once, under ``glcontext_``, so adding a
    backend is a change in one place."""

    @pytest.mark.parametrize('name', backends.WINDOWED)
    def test_only_glcontext_implements_it(self, name):
        duplicates = sorted(
            candidate for candidate in os.listdir(paths.TESTS)
            if candidate.endswith('_%s.py' % (name,))
            and candidate.startswith(('glcontext_', 'testdecorator_'))
        )
        assert duplicates == ['glcontext_%s.py' % (name,)], duplicates

    def test_no_per_backend_variant_of_the_fixture_is_left(self):
        """There were `basetestcase_glfw.py` and friends once, one fixture per
        windowing library.  A backend is wired up in `glcontext_<name>.py` and
        nowhere else."""
        left = sorted(
            candidate for candidate in os.listdir(paths.TESTS)
            if candidate.startswith(('basetestcase', 'testdecorator_'))
        )
        assert left == [], left


class TestTheDecoratorFinishesTheFrame:
    """``TEST_VISIBLE`` exists so somebody can look at what the suite drew, and
    the stand-alone check scripts are the ones most worth looking at.  A frame
    that is never presented cannot be looked at, and the dwell that holds it on
    screen belongs to the same teardown."""

    def _run_counting(self, hook):
        """Count calls to ``hook`` during one decorated run.

        Counted on the decorator's own case class, since that is where the
        backend mixin's override resolves -- patching the base would be
        shadowed by it and count nothing.
        """
        import testdecorator

        calls = []
        real = getattr(testdecorator._DecoratorCase, hook)

        def counted(self, *args, **named):
            calls.append(hook)
            return real(self, *args, **named)

        setattr(testdecorator._DecoratorCase, hook, counted)
        try:
            @testdecorator.gltest
            def draw():
                return None

            try:
                draw()
            except Exception as error:          # no GL here at all
                pytest.skip(str(error))
        finally:
            setattr(testdecorator._DecoratorCase, hook, real)
        return calls

    def test_the_frame_is_presented(self):
        assert self._run_counting('_swap') == ['_swap']

    def test_through_the_teardown_every_other_test_uses(self):
        """Not a swap of its own: the dwell and the cleanup order come with
        it."""
        assert self._run_counting('tearDown') == ['tearDown']


class TestAContextThatGoesIsForgotten:
    """The dispatch layer's table of resolved entry points is keyed by the GL
    context handle, and a handle is an address the driver hands out again --
    300 contexts through this fixture reuse 22 addresses on this machine. A
    context torn down without saying so leaves its resolved pointers behind for
    whichever context lands on its address next, which then answers about a
    context that no longer exists.

    Every backend has to say it, so the fixture says it for all of them.
    """

    def test_tearing_one_down_forgets_its_handle(self):
        import glcontext
        from glcontext_desktop import DesktopGLTestCaseBase

        forgotten = []

        class Case(glcontext.pick_backend(), DesktopGLTestCaseBase):
            def runTest(self):
                return None

        from OpenGL import _dispatch, platform

        real = _dispatch.forget_context
        handles = []
        try:
            _dispatch.forget_context = forgotten.append
            case = Case()
            case.setUp()
            handles.append(int(platform.PLATFORM.GetCurrentContext() or 0))
            case.tearDown()
            case.doCleanups()
        except Exception as error:
            pytest.skip('no GL context here: %s' % (error,))
        finally:
            _dispatch.forget_context = real
            # The spy stood in for the real one, so this context is still in
            # the table; give it back, or this test leaves behind exactly what
            # it exists to prevent.
            for handle in forgotten:
                real(handle)
        assert handles[0], 'no context handle to forget'
        assert forgotten == [handles[0]], (forgotten, handles)
