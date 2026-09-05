"""A context has to provide the version the case asked for, or the case skips.

Asking is not getting. GLFW refuses a request its driver cannot meet, so a
window either has the version or was never created; CGL does not -- a pixel
format naming the 3.2 core profile is accepted on a renderer that implements
2.1, and the context reports 2.1.

Calling into that gap is not a failed test but a dead process. macOS exports
every entry point from the framework whether or not the current context
implements it, so ``glDrawArraysInstanced`` on a 2.1 context resolves, is
called, and segfaults:

    Fatal Python error: Segmentation fault
      baseplatform.py:554 in __call__
      tests/gl/test_gl31.py:66 in test_instanced_and_copy

So the version is read back and compared, once, for every backend.
"""

import pytest
from glcontext import parse_gl_version, version_shortfall


class TestReadingTheVersionBack:
    @pytest.mark.parametrize('reported,expected', [
        ('4.6 (Core Profile) Mesa 25.2.8', (4, 6)),
        ('2.1 APPLE-20.0.44', (2, 1)),
        ('4.1 INTEL-22.5.13', (4, 1)),
        ('3.3.0 NVIDIA 550.54', (3, 3)),
        ('OpenGL ES 3.2 Mesa 25.2.8', (3, 2)),
        ('OpenGL ES-CM 1.1', (1, 1)),
    ])
    def test_the_number_is_read_off_the_front(self, reported, expected):
        """The string is a version followed by whatever the driver wants to
        say about itself, and OpenGL-ES puts its name first."""
        assert parse_gl_version(reported) == expected

    @pytest.mark.parametrize('reported', ['', 'nonsense', None])
    def test_a_string_with_no_version_in_it_is_unknown(self, reported):
        assert parse_gl_version(reported) is None


class TestWhetherItIsEnough:
    def test_the_version_asked_for_is_enough(self):
        assert version_shortfall('3.3 Mesa', (3, 3)) is None

    def test_so_is_more_than_it(self):
        assert version_shortfall('4.6 (Core Profile) Mesa', (3, 3)) is None

    def test_less_is_named_as_the_shortfall(self):
        """The crash above, before it is a crash: a 2.1 context answering a
        request for 3.3."""
        reason = version_shortfall('2.1 APPLE-20.0.44', (3, 3))
        assert reason and '2.1' in reason and '3.3' in reason

    def test_a_lower_minor_counts_too(self):
        assert version_shortfall('3.2 Mesa', (3, 3)) is not None

    def test_a_version_nobody_can_read_is_let_through(self):
        """Refusing to run on a driver whose string this cannot parse would
        turn an unknown into a skip on every one of its tests; the entry points
        still answer for themselves."""
        assert version_shortfall('nonsense', (3, 3)) is None

    def test_nothing_is_asked_of_a_case_that_pinned_no_version(self):
        assert version_shortfall('2.1 APPLE', None) is None


class TestTheFixtureActsOnIt:
    """The comparison is only worth having if setUp acts on it, and what it
    must do is skip: the case cannot run, and running it is the crash."""

    def _case(self, reported, wanted):
        import unittest

        import glcontext
        from glcontext_desktop import DesktopGLTestCaseBase

        class Case(glcontext.pick_backend(), DesktopGLTestCaseBase):
            profile = 'core'
            gl_version = wanted

            def getString(self, enum):
                from OpenGL import GL

                if enum == GL.GL_VERSION and reported is not None:
                    return reported
                return super().getString(enum)

            def runTest(self):
                return None

        case = Case()
        result = unittest.TestResult()
        case.run(result)
        return result

    def test_a_context_that_falls_short_skips(self):
        result = self._case('2.1 APPLE-20.0.44', (3, 3))
        if result.errors:
            pytest.skip('no GL context here: %s' % (result.errors[0][1][-300:],))
        assert result.skipped, result.failures
        assert 'needs 3.3' in result.skipped[0][1]

    def test_a_context_that_meets_it_runs(self):
        result = self._case(None, (2, 1))
        if result.errors:
            pytest.skip('no GL context here: %s' % (result.errors[0][1][-300:],))
        assert not result.skipped, result.skipped
        assert result.testsRun == 1


class TestACaseThatNeedsGluSaysSo:
    """GLU is a separate library, deprecated, and not always installed -- a
    container image with Mesa's GL in it often has no libGLU at all.  A case
    that calls into it there should say the library is missing, not raise
    NullFunctionError from its own setUp, which reads as a broken test rather
    than an absent dependency."""

    def _case(self, glu, needs_glu=True):
        import unittest

        import glcontext
        from glcontext_desktop import DesktopGLTestCaseBase

        class Case(glcontext.pick_backend(), DesktopGLTestCaseBase):
            pass

        Case.needs_glu = needs_glu
        Case.runTest = lambda self: None

        from OpenGL import platform

        # lazy_property caches into the instance, so an instance attribute is
        # what the code reads and what this replaces.
        missing = object()
        had = platform.PLATFORM.__dict__.get('GLU', missing)
        try:
            platform.PLATFORM.__dict__['GLU'] = glu
            case = Case()
            result = unittest.TestResult()
            case.run(result)
        finally:
            if had is missing:
                platform.PLATFORM.__dict__.pop('GLU', None)
            else:
                platform.PLATFORM.__dict__['GLU'] = had
        return result

    def test_it_skips_where_the_library_is_absent(self):
        result = self._case(glu=None)
        if result.errors:
            pytest.skip('no GL context here: %s' % (result.errors[0][1][-300:],))
        assert result.skipped, (result.failures, result.errors)
        assert 'GLU' in result.skipped[0][1]

    def test_it_runs_where_it_is_present(self):
        result = self._case(glu=object())
        if result.errors:
            pytest.skip('no GL context here: %s' % (result.errors[0][1][-300:],))
        assert not result.skipped, result.skipped

    def test_a_case_that_does_not_need_it_is_unaffected(self):
        result = self._case(glu=None, needs_glu=False)
        if result.errors:
            pytest.skip('no GL context here: %s' % (result.errors[0][1][-300:],))
        assert not result.skipped, result.skipped
