"""What a caller asks a Tk GL context for, and what each platform is told.

`ContextAttributes` is the request in one object; each platform turns it into
the attribute list its own API wants. Those translations are pure -- a list of
integers out of a dataclass -- so they are tested here without a display, a
window or a driver, which is what makes them worth testing at all: a wrong
constant in an attribute list produces "could not create a context" and nothing
else to go on.

See `plans/TK-WIDGET.md`.
"""

import pytest

from OpenGL.Tk.attributes import ContextAttributes


class TestWhatItAsksForByDefault:
    """The engine-era defaults: a core context you can put a shader in."""

    def test_it_asks_for_a_core_profile(self):
        assert ContextAttributes().profile == 'core'

    def test_it_asks_for_gl_3_3(self):
        assert ContextAttributes().version == (3, 3)

    def test_it_asks_for_double_buffering(self):
        assert ContextAttributes().doubleBuffer is True

    def test_it_asks_for_a_depth_buffer(self):
        assert ContextAttributes().depthSize == 24

    def test_a_core_profile_is_forward_compatible(self):
        assert ContextAttributes().forwardCompatible is True

    def test_a_compatibility_profile_is_not(self):
        assert ContextAttributes(profile='compatibility').forwardCompatible is False

    def test_saying_so_outranks_the_profile(self):
        assert ContextAttributes(profile='core',
                                 forwardCompatible=False).forwardCompatible is False


class TestTheProfileNames:
    @pytest.mark.parametrize('name', ['core', 'compatibility', 'legacy'])
    def test_the_three_it_knows(self, name):
        assert ContextAttributes(profile=name).profile == name

    def test_anything_else_is_refused_where_it_is_written(self):
        """Rather than at context creation, where the message would be the
        driver's refusal of an attribute list nobody can read."""
        with pytest.raises(ValueError) as raised:
            ContextAttributes(profile='modern')
        assert 'modern' in str(raised.value)
        assert 'core' in str(raised.value)

    def test_legacy_asks_for_no_version_at_all(self):
        """Which is how a driver with no create-context extension is asked --
        and what the fixed-function widgets want."""
        assert ContextAttributes(profile='legacy').version is None


class TestWhenAProfileIsAThingToAskFor:
    """**A profile is a GL 3.2 idea.**  Asked for a version below that, a
    driver refuses the whole request rather than ignoring the part of it that
    means nothing -- so a request for "core 2.1", which every toolkit answers
    with a plain 2.1 context, came back as an X ``BadValue`` and no context at
    all.
    """

    def test_it_applies_from_3_2(self):
        assert ContextAttributes(version=(3, 2)).profileApplies() is True

    def test_it_does_not_below_that(self):
        assert ContextAttributes(version=(2, 1)).profileApplies() is False
        assert ContextAttributes(version=(3, 1)).profileApplies() is False

    def test_a_legacy_request_never_names_one(self):
        assert ContextAttributes(profile='legacy').profileApplies() is False

    def test_nor_does_one_with_no_version(self):
        assert ContextAttributes(version=None).profileApplies() is False

    def test_forward_compatible_applies_from_3_0(self):
        assert ContextAttributes(version=(3, 0),
                                 forwardCompatible=True).forwardCompatibleApplies()
        assert not ContextAttributes(version=(2, 1),
                                     forwardCompatible=True).forwardCompatibleApplies()

    def test_not_asking_for_it_is_not_asking_for_it(self):
        assert not ContextAttributes(forwardCompatible=False) \
            .forwardCompatibleApplies()


class TestTheGLXAttributeLists:
    """`glXChooseFBConfig` takes one list and `glXCreateContextAttribsARB`
    another; both end in None/0."""

    def _config(self, **named):
        from OpenGL.Tk.glx import configAttributes
        return configAttributes(ContextAttributes(**named))

    def _context(self, **named):
        from OpenGL.Tk.glx import contextAttributes
        return contextAttributes(ContextAttributes(**named))

    def _paired(self, attributes):
        """The list as {name: value}, dropping the terminator."""
        return dict(zip(attributes[:-1:2], attributes[1:-1:2]))

    def test_the_config_list_ends_in_the_terminator(self):
        from OpenGL import GL
        assert self._config()[-1] == GL.GL_NONE

    def test_it_asks_for_a_window_it_can_render_into(self):
        from OpenGL import GLX
        paired = self._paired(self._config())
        assert paired[GLX.GLX_DRAWABLE_TYPE] == GLX.GLX_WINDOW_BIT
        assert paired[GLX.GLX_RENDER_TYPE] == GLX.GLX_RGBA_BIT

    def test_the_buffer_sizes_are_passed_on(self):
        from OpenGL import GLX
        paired = self._paired(self._config(depthSize=16, stencilSize=8,
                                           alphaSize=8))
        assert paired[GLX.GLX_DEPTH_SIZE] == 16
        assert paired[GLX.GLX_STENCIL_SIZE] == 8
        assert paired[GLX.GLX_ALPHA_SIZE] == 8

    def test_a_single_buffered_request_says_so(self):
        from OpenGL import GLX
        assert self._paired(self._config(doubleBuffer=False))[
            GLX.GLX_DOUBLEBUFFER] == 0
        assert self._paired(self._config())[GLX.GLX_DOUBLEBUFFER] == 1

    def test_multisampling_is_asked_for_only_when_wanted(self):
        from OpenGL import GLX
        assert GLX.GLX_SAMPLES not in self._paired(self._config())
        paired = self._paired(self._config(samples=4))
        assert paired[GLX.GLX_SAMPLES] == 4
        assert paired[GLX.GLX_SAMPLE_BUFFERS] == 1

    def test_stereo_is_asked_for_only_when_wanted(self):
        from OpenGL import GLX
        assert GLX.GLX_STEREO not in self._paired(self._config())
        assert self._paired(self._config(stereo=True))[GLX.GLX_STEREO] == 1

    def test_the_context_list_carries_the_version_and_the_profile(self):
        from OpenGL.GLX.ARB import create_context, create_context_profile
        paired = self._paired(self._context(version=(4, 1)))
        assert paired[create_context.GLX_CONTEXT_MAJOR_VERSION_ARB] == 4
        assert paired[create_context.GLX_CONTEXT_MINOR_VERSION_ARB] == 1
        assert (paired[create_context_profile.GLX_CONTEXT_PROFILE_MASK_ARB]
                == create_context_profile.GLX_CONTEXT_CORE_PROFILE_BIT_ARB)

    def test_a_compatibility_request_asks_for_that_bit(self):
        from OpenGL.GLX.ARB import create_context_profile
        paired = self._paired(self._context(profile='compatibility'))
        assert (paired[create_context_profile.GLX_CONTEXT_PROFILE_MASK_ARB]
                == create_context_profile.GLX_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB)

    def test_a_core_request_is_forward_compatible(self):
        from OpenGL.GLX.ARB import create_context
        paired = self._paired(self._context())
        assert (paired[create_context.GLX_CONTEXT_FLAGS_ARB]
                & create_context.GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB)

    def test_a_debug_context_asks_for_the_debug_bit(self):
        from OpenGL.GLX.ARB import create_context
        paired = self._paired(self._context(debug=True))
        assert (paired[create_context.GLX_CONTEXT_FLAGS_ARB]
                & create_context.GLX_CONTEXT_DEBUG_BIT_ARB)

    def test_a_legacy_request_asks_for_nothing_at_all(self):
        """There is no version and no profile to ask for, so the list is the
        terminator alone -- and the caller uses the old entry point."""
        assert self._context(profile='legacy') == [0]

    def test_a_version_below_3_2_names_no_profile(self):
        """There is none to name, and a driver handed one refuses the lot."""
        from OpenGL.GLX.ARB import create_context, create_context_profile

        paired = self._paired(self._context(version=(2, 1)))
        assert create_context_profile.GLX_CONTEXT_PROFILE_MASK_ARB not in paired
        assert paired[create_context.GLX_CONTEXT_MAJOR_VERSION_ARB] == 2
        assert create_context.GLX_CONTEXT_FLAGS_ARB not in paired


class TestTheWGLAttributeLists:
    """Windows takes the same two questions as `wglChoosePixelFormatARB` and
    `wglCreateContextAttribsARB`."""

    def _format(self, **named):
        from OpenGL.Tk.win32 import pixelFormatAttributes
        return pixelFormatAttributes(ContextAttributes(**named))

    def _context(self, **named):
        from OpenGL.Tk.win32 import contextAttributes
        return contextAttributes(ContextAttributes(**named))

    def _paired(self, attributes):
        return dict(zip(attributes[:-1:2], attributes[1:-1:2]))

    def test_the_format_list_ends_in_the_terminator(self):
        assert self._format()[-1] == 0

    def test_it_asks_for_a_window_it_can_render_into(self):
        from OpenGL.WGL.ARB import pixel_format
        paired = self._paired(self._format())
        assert paired[pixel_format.WGL_DRAW_TO_WINDOW_ARB]
        assert paired[pixel_format.WGL_SUPPORT_OPENGL_ARB]

    def test_the_buffer_sizes_are_passed_on(self):
        from OpenGL.WGL.ARB import pixel_format
        paired = self._paired(self._format(depthSize=16, stencilSize=8,
                                           alphaSize=8))
        assert paired[pixel_format.WGL_DEPTH_BITS_ARB] == 16
        assert paired[pixel_format.WGL_STENCIL_BITS_ARB] == 8
        assert paired[pixel_format.WGL_ALPHA_BITS_ARB] == 8

    def test_a_single_buffered_request_says_so(self):
        from OpenGL.WGL.ARB import pixel_format
        assert self._paired(self._format(doubleBuffer=False))[
            pixel_format.WGL_DOUBLE_BUFFER_ARB] == 0

    def test_multisampling_is_asked_for_only_when_wanted(self):
        from OpenGL.WGL.ARB import multisample, pixel_format
        assert multisample.WGL_SAMPLES_ARB not in self._paired(self._format())
        paired = self._paired(self._format(samples=8))
        assert paired[multisample.WGL_SAMPLES_ARB] == 8
        assert paired[multisample.WGL_SAMPLE_BUFFERS_ARB] == 1
        assert pixel_format.WGL_PIXEL_TYPE_ARB in paired

    def test_the_context_list_carries_the_version_and_the_profile(self):
        from OpenGL.WGL.ARB import create_context, create_context_profile
        paired = self._paired(self._context(version=(4, 6)))
        assert paired[create_context.WGL_CONTEXT_MAJOR_VERSION_ARB] == 4
        assert paired[create_context.WGL_CONTEXT_MINOR_VERSION_ARB] == 6
        assert (paired[create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB]
                == create_context_profile.WGL_CONTEXT_CORE_PROFILE_BIT_ARB)

    def test_a_legacy_request_asks_for_nothing_at_all(self):
        assert self._context(profile='legacy') == [0]

    def test_a_version_below_3_2_names_no_profile(self):
        from OpenGL.WGL.ARB import create_context, create_context_profile

        paired = self._paired(self._context(version=(2, 1)))
        assert create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB not in paired
        assert paired[create_context.WGL_CONTEXT_MAJOR_VERSION_ARB] == 2
