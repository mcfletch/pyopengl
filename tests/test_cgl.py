"""What ``OpenGL.CGL`` asks macOS for, checked without a Mac to ask.

The attribute list is where the decisions live -- which profile, which
renderer, how many bits of each buffer -- and it is a list of integers built
from arguments, so it can be read back here. What cannot be checked without
Apple's implementation is only whether a machine *offers* what was asked for,
and that is one call with the list this file pins.

The constants are Apple's, from ``CGLTypes.h`` and ``CGLRenderers.h``. A wrong
one is not a failed call but a different question asked of the driver, so the
few that carry meaning are written down rather than assumed.
"""

import sys

import pytest

from OpenGL import CGL


def attributes(**named):
    """The attribute list, minus its terminator, as (attribute, value) is hard
    to read positionally."""
    built = CGL.pixel_format_attributes(**named)
    assert built[-1] == 0, 'the list has to tell CGL where it ends'
    return built[:-1]


class TestTheProfileIsAlwaysNamed:
    """macOS gives a legacy 2.1 context unless asked otherwise, and there is no
    compatibility profile above it -- so which profile is wanted is never left
    to a default."""

    @pytest.mark.parametrize('profile,value', [
        ('legacy', 0x1000),
        ('core3', 0x3200),
        ('core4', 0x4100),
    ])
    def test_each_profile_asks_for_its_own_version(self, profile, value):
        built = attributes(profile=profile)
        assert built[0] == CGL.kCGLPFAOpenGLProfile
        assert built[1] == value

    def test_a_profile_nobody_offers_is_a_programming_error(self):
        with pytest.raises(ValueError, match='sideways'):
            CGL.pixel_format_attributes(profile='sideways')


class TestAskingForARenderer:
    def test_acceleration_is_asked_for_by_name(self):
        assert CGL.kCGLPFAAccelerated in attributes(renderer='accelerated')

    def test_no_preference_asks_for_neither(self):
        """The case a machine with no accelerated renderer needs: asking for
        acceleration where there is none fails rather than falling back."""
        built = attributes(renderer='any')
        assert CGL.kCGLPFAAccelerated not in built
        assert CGL.kCGLPFARendererID not in built

    def test_software_names_the_cpu_renderer(self):
        """There is no "not accelerated" attribute, so the CPU renderer is
        asked for by its id."""
        built = attributes(renderer='software')
        assert CGL.kCGLPFAAccelerated not in built
        index = built.index(CGL.kCGLPFARendererID)
        assert built[index + 1] == CGL.kCGLRendererGenericFloatID

    def test_a_renderer_kind_nobody_offers_is_a_programming_error(self):
        with pytest.raises(ValueError, match='sideways'):
            CGL.pixel_format_attributes(renderer='sideways')


class TestTheBuffers:
    def test_the_sizes_asked_for_are_the_sizes_given(self):
        built = attributes(color_size=32, alpha_size=0, depth_size=16,
                           stencil_size=0)
        for attribute, size in (
            (CGL.kCGLPFAColorSize, 32),
            (CGL.kCGLPFAAlphaSize, 0),
            (CGL.kCGLPFADepthSize, 16),
            (CGL.kCGLPFAStencilSize, 0),
        ):
            assert built[built.index(attribute) + 1] == size

    def test_a_single_buffered_format_does_not_ask_for_two(self):
        """Nothing is presented from a context with no drawable, so the second
        buffer is a buffer nobody reads."""
        assert CGL.kCGLPFADoubleBuffer not in attributes()

    def test_double_buffering_can_still_be_asked_for(self):
        assert CGL.kCGLPFADoubleBuffer in attributes(double_buffer=True)

    def test_no_multisampling_is_asked_for_by_default(self):
        assert CGL.kCGLPFASamples not in attributes()

    def test_multisampling_asks_for_a_buffer_to_put_it_in(self):
        built = attributes(samples=4)
        assert built[built.index(CGL.kCGLPFASampleBuffers) + 1] == 1
        assert built[built.index(CGL.kCGLPFASamples) + 1] == 4


class TestTheConstantsAreApples:
    """A wrong value here is not a failed call: it is a different question put
    to the driver, answered plausibly and wrongly."""

    @pytest.mark.parametrize('name,value', [
        ('kCGLPFAAccelerated', 73),
        ('kCGLPFARendererID', 70),
        ('kCGLPFAOpenGLProfile', 99),
        ('kCGLPFAColorSize', 8),
        ('kCGLPFAAlphaSize', 11),
        ('kCGLPFADepthSize', 12),
        ('kCGLPFAStencilSize', 13),
        ('kCGLPFADoubleBuffer', 5),
        ('kCGLPFASampleBuffers', 55),
        ('kCGLPFASamples', 56),
        ('kCGLRendererGenericFloatID', 0x00020400),
        ('kCGLOGLPVersion_Legacy', 0x1000),
        ('kCGLOGLPVersion_3_2_Core', 0x3200),
        ('kCGLOGLPVersion_GL4_Core', 0x4100),
    ])
    def test_it_has_apples_value(self, name, value):
        assert getattr(CGL, name) == value


class TestWhatEachProfilePromises:
    """CGL accepts a pixel format naming a profile the renderer cannot provide
    and answers with a lower context rather than refusing, so what a profile
    promises has to be written down to be compared against."""

    @pytest.mark.parametrize('profile,version', [
        ('legacy', (2, 1)),
        ('core3', (3, 2)),
        ('core4', (4, 1)),
    ])
    def test_each_names_the_version_it_provides(self, profile, version):
        assert CGL.PROFILE_VERSIONS[profile] == version

    def test_every_profile_has_one(self):
        assert set(CGL.PROFILE_VERSIONS) == set(CGL.PROFILES)

    def test_a_downgraded_core_profile_is_detected(self):
        """The condition that segfaulted: a core profile answering with 2.1,
        after which a GL 3.1 entry point resolves and is called."""
        from glcontext import version_shortfall

        assert version_shortfall('2.1 APPLE-20.0.44',
                                 CGL.PROFILE_VERSIONS['core3'])

    def test_and_a_profile_that_kept_its_promise_is_not(self):
        from glcontext import version_shortfall

        assert version_shortfall('4.1 APPLE-20.0.44',
                                 CGL.PROFILE_VERSIONS['core4']) is None


class TestWhatTheMachineCanRender:
    """Asked of the machine rather than inferred from what a context turned out
    to be: ``CGLQueryRendererInfo`` describes every renderer without creating
    anything, and says which GL major version each supports.  On a machine
    nobody can log into, that is the difference between knowing what is there
    and guessing from a crash."""

    def info(self, **overrides):
        fields = {
            'index': 0,
            'renderer_id': CGL.kCGLRendererAppleSWID,
            'accelerated': False,
            'online': False,
            'major_gl_version': 2,
            'video_memory': 0,
        }
        fields.update(overrides)
        return CGL.RendererInfo(**fields)

    def test_a_renderer_that_is_not_accelerated_is_software(self):
        assert self.info(accelerated=False).software

    def test_and_one_that_is_is_not(self):
        assert not self.info(accelerated=True).software

    def test_it_says_the_gl_major_it_supports(self):
        assert self.info(major_gl_version=4).major_gl_version == 4

    def test_the_repr_names_what_a_reader_needs(self):
        text = repr(self.info(major_gl_version=2, accelerated=False))
        assert 'software' in text and 'GL 2' in text

    @pytest.mark.parametrize('name,value', [
        ('kCGLRPRendererID', 70),
        ('kCGLRPAccelerated', 73),
        ('kCGLRPOnline', 129),
        ('kCGLRPVideoMemoryMegabytes', 131),
        ('kCGLRPMajorGLVersion', 133),
    ])
    def test_the_property_constants_are_apples(self, name, value):
        assert getattr(CGL, name) == value

    def test_enumerating_answers_or_says_there_is_no_cgl(self):
        try:
            found = CGL.renderers()
        except CGL.CGLError:
            pytest.skip('no CGL on this platform')
        assert isinstance(found, tuple)


class TestAnErrorSaysWhichCallAndWhy:
    def test_it_names_the_call_and_the_error(self):
        error = CGL.CGLError('CGLCreateContext', 10004)
        assert 'CGLCreateContext' in str(error)
        assert 'kCGLBadContext' in str(error)

    def test_the_code_is_kept_for_a_caller_to_branch_on(self):
        """"this machine offers no such format" and "the arguments were wrong"
        are different answers, and a caller should not have to read English to
        tell them apart."""
        assert CGL.CGLError('CGLChoosePixelFormat', 10002).code == 10002

    def test_an_unknown_code_still_produces_a_message(self):
        assert '4242' in str(CGL.CGLError('CGLSetCurrentContext', 4242))


class TestItImportsWhereThereIsNoCGL:
    """The attribute half is pure, so it is importable and usable anywhere --
    which is what lets the decisions above be tested off a Mac at all."""

    def test_the_module_imports(self):
        assert CGL.PROFILES and CGL.RENDERER_KINDS

    @pytest.mark.skipif(sys.platform == 'darwin',
                        reason='this is the behaviour away from CGL')
    def test_reaching_for_the_library_is_what_fails(self):
        """And it fails as a CGL error, so a caller has one thing to catch
        whether the machine has no CGL or CGL refused the request."""
        with pytest.raises(CGL.CGLError):
            CGL.library()
