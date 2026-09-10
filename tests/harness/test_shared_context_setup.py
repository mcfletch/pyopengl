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
    """The point of the unification: a headless runner is what CI has.

    Which backend that means is a question of platform -- EGL on Linux, CGL on
    macOS, a WGL pbuffer on Windows -- so these ask :mod:`backends` for the one
    this machine has rather than naming it.  Naming ``egl`` here ran the Linux
    platform module on Windows, which found no GL library, skipped all
    twenty-eight cases and left the assertion measuring nothing.
    """

    #: The headless backend of the machine running this, or None where it has
    #: none.  A platform with no headless backend cannot answer the question.
    HEADLESS = backends.headless_for()

    #: How long the child gets.  It runs the whole of ``tests/gl`` -- four
    #: minutes on a slow machine -- and the bound is generous rather than
    #: tight.  What it is for is the case where the child does not finish at
    #: all: a GL call that blocks takes this process with it, and a suite that
    #: hangs after its last line of output says nothing about what went wrong.
    CHILD_TIMEOUT = 900

    def _run(self, windowing):
        environment = dict(os.environ)
        environment['TEST_WINDOWING'] = windowing
        environment['TEST_VISIBLE'] = '0'
        try:
            return subprocess.run(
                # `--tb=short`: what this case reports is the child's output,
                # and without a traceback in it a failure here says a name
                # and nothing else -- which costs a whole run to learn.
                [sys.executable, '-m', 'pytest', '-q', '--no-header',
                 '--tb=short', '-p', 'no:randomly',
                 os.path.join('tests', 'gl')],
                cwd=ROOT, env=environment, capture_output=True, text=True,
                check=False, timeout=self.CHILD_TIMEOUT)
        except subprocess.TimeoutExpired as expired:
            pytest.fail(
                'the child running tests/gl under %s did not finish within '
                '%d seconds; its output so far:\n%s'
                % (windowing, self.CHILD_TIMEOUT,
                   (expired.stdout or b'')[-2000:]))

    @staticmethod
    def _why(completed):
        """What the child said about its failures.

        Leading with the lines naming them, because the child prints its
        tracebacks *before* the summary of what it skipped -- and `tests/gl`
        skips several hundred cases on any one driver, so the tail of its
        output is those and not the failure.
        """
        named = [
            line for line in completed.stdout.splitlines()
            if line.startswith(('FAILED', 'ERROR'))
        ]
        return '%s\n\nthe tail of its output:\n%s' % (
            '\n'.join(named) or '(it named no failure)',
            completed.stdout[-6000:],
        )

    def test_this_platform_has_a_headless_backend(self):
        """The premise of the two below, said once and by name: without one,
        every headless claim this suite makes is untested here."""
        assert self.HEADLESS in backends.HEADLESS, (
            'no headless backend for %s' % (sys.platform,))

    def test_the_gl_suite_is_not_skipped_wholesale(self):
        completed = self._run(self.HEADLESS)
        assert 'unavailable under the headless' not in completed.stdout, (
            'tests/gl still skips under %s: %s'
            % (self.HEADLESS, completed.stdout[-2000:]))

    def test_and_it_actually_passes_there(self):
        completed = self._run(self.HEADLESS)
        for absent in ('no usable GL', 'no EGL', 'no offscreen'):
            if absent in completed.stdout:
                pytest.skip('no headless GL on this machine')
        assert ' passed' in completed.stdout, self._why(completed)
        assert 'failed' not in completed.stdout, self._why(completed)


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
        # That it was said, and about this context, rather than how many times
        # or about how many contexts.  Retiring a table twice is retiring it
        # and then finding nothing to retire, and a backend may sit on a
        # library that owns contexts of its own and retires those too -- which
        # it has to, because a caller reaching for it directly has no fixture
        # doing it for them.  `OpenGL.WGL.offscreen.OffscreenContext` retires
        # the one it hands out; `OpenGL.Tk` retires that one and the two
        # throwaway contexts WGL needs to look an extension up through, whose
        # handles the driver hands out again as readily as any other.
        assert forgotten, (forgotten, handles)
        assert handles[0] in forgotten, (forgotten, handles)
