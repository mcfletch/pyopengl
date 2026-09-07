"""What the headless macOS backend will and will not serve.

Which CGL profile answers a test's ``api`` / ``profile`` / ``gl_version`` is a
decision over three arguments, so it is a plain function and is checked here,
on any platform. What is left for a Mac is one CGL call with the answer.

The two refusals matter as much as the matches. A backend that quietly served a
legacy 2.1 context to a case asking for compatibility 4.5 would let that case
pass having tested the wrong thing; skipping says the platform has no such
context, which is the fact.
"""

import glcontext_cgl
import pytest
from glcontext_cgl import profile_for


def served(**named):
    """The profile chosen, asserting that one was."""
    request = {'api': 'gl', 'profile': 'compatibility', 'gl_version': (2, 1)}
    request.update(named)
    profile, refusal = profile_for(**request)
    assert profile is not None, refusal
    return profile


def refused(**named):
    """The reason given, asserting that the request was refused."""
    request = {'api': 'gl', 'profile': 'compatibility', 'gl_version': (2, 1)}
    request.update(named)
    profile, refusal = profile_for(**request)
    assert profile is None, 'expected a refusal, got %r' % (profile,)
    return refusal


class TestTheDefaultRequest:
    def test_it_is_the_legacy_profile(self):
        """``ContextTestCase`` asks for compatibility 2.1, which on macOS is
        the legacy profile -- and the only one with fixed function in it."""
        assert served() == 'legacy'


class TestACoreProfile:
    @pytest.mark.parametrize('version', [(3, 2), (3, 3), (4, 0)])
    def test_below_four_one_it_is_the_3_2_profile(self, version):
        assert served(profile='core', gl_version=version) == 'core3'

    @pytest.mark.parametrize('version', [(4, 1), (4, 5), (4, 6)])
    def test_from_four_one_it_is_the_gl4_profile(self, version):
        """macOS stops at 4.1, and asking for 4.5 gets the 4.1 profile: the
        context is real, and a test wanting something 4.5 added finds it
        missing at the call rather than at creation."""
        assert served(profile='core', gl_version=version) == 'core4'

    def test_a_core_profile_below_3_2_does_not_exist(self):
        assert '3.2' in refused(profile='core', gl_version=(2, 1))


class TestWhatMacosCannotServe:
    def test_there_is_no_gles_through_cgl(self):
        assert 'OpenGL-ES' in refused(api='gles')

    def test_es_is_spelt_both_ways(self):
        assert refused(api='es') is not None

    @pytest.mark.parametrize('version', [(3, 2), (4, 5)])
    def test_no_compatibility_profile_above_two_one(self, version):
        """The refusal names the version asked for, since the point of reading
        a skip is finding out what the case wanted."""
        reason = refused(profile='compatibility', gl_version=version)
        assert 'compatibility' in reason
        assert '%d.%d' % version in reason


class TestTheBackendIsSelectable:
    def test_the_name_is_recognised(self):
        import glcontext

        assert 'cgl' in glcontext._ALL_BACKENDS

    def test_it_is_headless(self):
        """There is no window, so nothing can be shown and nothing dwells."""
        assert glcontext_cgl.CGLBackend.visible is False

    def test_it_names_itself(self):
        assert glcontext_cgl.CGLBackend.backend_name == 'cgl'
