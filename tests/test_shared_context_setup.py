"""One mechanism for putting a GL context under a test.

:class:`glcontext.ContextTestCase` with a backend mixin per windowing system is
that mechanism, and ``basetestcase.BaseTest`` and the ``testdecorator.gltest``
decorator are both built on it.

A second mechanism costs more than the duplication: one that names a windowing
library itself cannot render where there is no window, and a headless runner is
what CI has. These hold the two to the shared fixture, so the seventy tests
built on them keep running there.
"""

import os
import subprocess
import sys

import backends
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


class TestTheLegacyBaseIsTheSharedOne:
    def test_base_test_is_a_context_test_case(self):
        import basetestcase
        import glcontext

        assert issubclass(basetestcase.BaseTest, glcontext.ContextTestCase)

    def test_it_keeps_the_size_the_legacy_tests_expect(self):
        """Their reference values were measured in a 300x300 window."""
        import basetestcase

        assert basetestcase.BaseTest.width == 300
        assert basetestcase.BaseTest.height == 300

    def test_it_asks_for_the_profile_those_tests_draw_with(self):
        """They call glBegin, the matrix stack and the GLU quadrics."""
        import basetestcase

        assert basetestcase.BaseTest.profile == 'compatibility'

    def test_the_gl_namespace_is_still_exported(self):
        """The legacy modules do ``from basetestcase import *`` and expect the
        GL entry points to arrive with it."""
        import basetestcase

        for name in ('glClear', 'glBegin', 'gluPerspective', 'GL_TRIANGLES'):
            assert hasattr(basetestcase, name), name


class TestItRunsWhereThereIsNoWindow:
    """The point of the unification: a headless runner is what CI has."""

    def _run(self, windowing):
        environment = dict(os.environ)
        environment['TEST_WINDOWING'] = windowing
        environment['TEST_VISIBLE'] = '0'
        return subprocess.run(
            [sys.executable, '-m', 'pytest', '-q', '--no-header', '-p',
             'no:randomly', os.path.join('tests', 'test_core.py')],
            cwd=ROOT, env=environment, capture_output=True, text=True,
            check=False)

    @pytest.mark.parametrize('windowing', ['egl'])
    def test_the_legacy_suite_is_not_skipped_wholesale(self, windowing):
        completed = self._run(windowing)
        assert 'unavailable under the headless' not in completed.stdout, (
            'test_core still skips under %s: %s'
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
            candidate for candidate in os.listdir(HERE)
            if candidate.endswith('_%s.py' % (name,))
            and candidate.startswith(('glcontext_', 'basetestcase_',
                                      'testdecorator_'))
        )
        assert duplicates == ['glcontext_%s.py' % (name,)], duplicates

    def test_the_legacy_per_backend_modules_are_gone(self):
        left = sorted(
            candidate for candidate in os.listdir(HERE)
            if candidate.startswith(('basetestcase_', 'testdecorator_'))
        )
        assert left == [], left
