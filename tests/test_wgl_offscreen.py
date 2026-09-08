"""Offscreen OpenGL on Windows: what is asked for, and asking for it.

Two layers, as elsewhere in this suite:

  * pure Python -- the attribute lists a request becomes.  This is where the
    decisions live, and it runs everywhere: no Windows, no driver, no GPU.  A
    Linux run therefore holds the Windows path to its contract, which matters
    because WGL is the namespace an ordinary run never reaches.
  * real -- a pbuffer, a context on it, and pixels read back.  Windows only,
    and skipped where the driver offers no pbuffers.

The pure half is worth holding closely.  ``WGL_DRAW_TO_PBUFFER_ARB`` missing
from the format request produces a format that looks fine and a pbuffer the
driver then refuses; a profile bit sent with a request below GL 3.2 makes the
driver refuse the whole context.  Neither is visible in a passing run on a
machine that has no WGL.
"""

import ctypes
import os
import sys

import pytest

from OpenGL.WGL import offscreen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

windows_only = pytest.mark.skipif(
    sys.platform != 'win32', reason='WGL is the Windows binding for OpenGL')


def pairs(attributes):
    """The token/value list as a dict, ignoring the zero terminator."""
    values = list(attributes)
    return dict(zip(values[:-1:2], values[1::2], strict=True))


class TestTheModuleIsDocumented:
    """A public module nobody can find is a module nobody uses."""

    def test_there_is_a_page_for_it(self):
        page = os.path.join(ROOT, 'documentation', 'wgl-offscreen.html')
        assert os.path.exists(page), page
        with open(page, encoding='utf-8') as handle:
            text = handle.read()
        for named in (
            'OpenGL.WGL.offscreen',
            'headless_context',
            'WGL_ARB_pbuffer',
            'wglCreatePbufferARB',
            'available',
            'bootstrap',
        ):
            assert named in text, named

    def test_the_package_offers_it_without_a_deeper_import(self):
        from OpenGL import WGL

        assert WGL.offscreen is not None
        assert callable(WGL.offscreen.headless_context)


class TestThePixelFormatRequest:
    """What ``wglChoosePixelFormatARB`` is asked for."""

    def test_it_asks_to_draw_to_a_pbuffer(self):
        """The one thing the old ChoosePixelFormat cannot say, and the reason
        the ARB call is used at all."""
        from OpenGL.WGL.ARB import pbuffer

        assert pairs(offscreen.pixel_format_attributes())[
            pbuffer.WGL_DRAW_TO_PBUFFER_ARB] == 1

    def test_depth_and_stencil_come_from_the_request(self):
        from OpenGL.WGL.ARB import pixel_format

        asked = pairs(offscreen.pixel_format_attributes(
            depth_bits=32, stencil_bits=8))
        assert asked[pixel_format.WGL_DEPTH_BITS_ARB] == 32
        assert asked[pixel_format.WGL_STENCIL_BITS_ARB] == 8

    @pytest.mark.parametrize('name,token', [
        ('alpha_bits', 'WGL_ALPHA_BITS_ARB'),
        ('depth_bits', 'WGL_DEPTH_BITS_ARB'),
        ('stencil_bits', 'WGL_STENCIL_BITS_ARB'),
    ])
    def test_a_buffer_of_no_bits_is_left_out(self, name, token):
        """Left out rather than asked for as zero, so the driver picks: a
        format is a match if it is *at least* what was asked for, and asking
        for zero of something is not the same as not asking."""
        from OpenGL.WGL.ARB import pixel_format

        asked = pairs(offscreen.pixel_format_attributes(**{name: 0}))
        assert getattr(pixel_format, token) not in asked

    def test_multisampling_is_requested_only_when_asked_for(self):
        from OpenGL.WGL.ARB import multisample

        assert pairs(offscreen.pixel_format_attributes(samples=4))[
            multisample.WGL_SAMPLES_ARB] == 4
        assert multisample.WGL_SAMPLES_ARB not in pairs(
            offscreen.pixel_format_attributes())

    def test_single_buffering_is_asked_for_explicitly(self):
        """There is nothing to present to, so a back buffer nobody swaps is
        memory spent on nothing -- and "at least what was asked for" means
        saying so is the only way not to get one."""
        from OpenGL.WGL.ARB import pixel_format

        assert pairs(offscreen.pixel_format_attributes())[
            pixel_format.WGL_DOUBLE_BUFFER_ARB] == 0
        assert pairs(offscreen.pixel_format_attributes(double_buffer=True))[
            pixel_format.WGL_DOUBLE_BUFFER_ARB] == 1

    def test_acceleration_is_demanded_by_default(self):
        from OpenGL.WGL.ARB import pixel_format

        assert pairs(offscreen.pixel_format_attributes())[
            pixel_format.WGL_ACCELERATION_ARB
        ] == pixel_format.WGL_FULL_ACCELERATION_ARB

    def test_any_acceleration_names_none(self):
        """A machine whose adapter is virtualised or unusual may have no format
        calling itself fully accelerated, and rendering slowly beats not
        rendering."""
        from OpenGL.WGL.ARB import pixel_format

        assert pixel_format.WGL_ACCELERATION_ARB not in pairs(
            offscreen.pixel_format_attributes(acceleration='any'))

    def test_an_acceleration_nobody_offers_is_refused_by_name(self):
        with pytest.raises(ValueError) as raised:
            offscreen.pixel_format_attributes(acceleration='sideways')
        for name in offscreen.ACCELERATION_KINDS:
            assert name in str(raised.value)

    def test_the_list_is_terminated(self):
        assert offscreen.pixel_format_attributes()[-1] == 0


class TestTheContextRequest:
    """What ``wglCreateContextAttribsARB`` is asked for."""

    def test_the_version_asked_for_is_the_version_requested(self):
        from OpenGL.WGL.ARB import create_context

        asked = pairs(offscreen.context_attributes(version=(4, 6)))
        assert asked[create_context.WGL_CONTEXT_MAJOR_VERSION_ARB] == 4
        assert asked[create_context.WGL_CONTEXT_MINOR_VERSION_ARB] == 6

    @pytest.mark.parametrize('profile,bit', [
        ('core', 'WGL_CONTEXT_CORE_PROFILE_BIT_ARB'),
        ('compatibility', 'WGL_CONTEXT_COMPATIBILITY_PROFILE_BIT_ARB'),
    ])
    def test_a_named_profile_sets_its_bit(self, profile, bit):
        from OpenGL.WGL.ARB import create_context_profile

        asked = pairs(offscreen.context_attributes(profile=profile))
        assert asked[create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB] == (
            getattr(create_context_profile, bit))

    def test_legacy_names_no_profile_at_all(self):
        """The profile mask did not exist below GL 3.2, and a driver handed one
        there refuses the whole request rather than ignoring it."""
        from OpenGL.WGL.ARB import create_context_profile

        assert create_context_profile.WGL_CONTEXT_PROFILE_MASK_ARB not in pairs(
            offscreen.context_attributes(profile='legacy', version=(2, 1)))

    def test_no_flags_word_is_sent_when_no_flag_is_set(self):
        from OpenGL.WGL.ARB import create_context

        assert create_context.WGL_CONTEXT_FLAGS_ARB not in pairs(
            offscreen.context_attributes())

    def test_debug_and_forward_compatible_share_the_flags_word(self):
        from OpenGL.WGL.ARB import create_context

        asked = pairs(offscreen.context_attributes(
            debug=True, forward_compatible=True))
        assert asked[create_context.WGL_CONTEXT_FLAGS_ARB] == (
            create_context.WGL_CONTEXT_DEBUG_BIT_ARB
            | create_context.WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB)

    def test_a_profile_nobody_offers_is_refused_by_name(self):
        with pytest.raises(ValueError) as raised:
            offscreen.context_attributes(profile='sideways')
        for name in offscreen.PROFILES:
            assert name in str(raised.value)

    def test_the_list_is_terminated(self):
        assert offscreen.context_attributes()[-1] == 0


class TestWhatItSaysWhereThereIsNoWGL:
    """The module imports anywhere -- that is what lets the two classes above
    run on a Linux runner -- so reaching the Windows half from there has to say
    what was reached for."""

    def test_the_structures_are_the_size_windows_declares(self):
        """A PIXELFORMATDESCRIPTOR whose nSize is wrong is rejected, and this
        is checkable without Windows."""
        assert ctypes.sizeof(offscreen.PIXELFORMATDESCRIPTOR) == 40

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason='this is what the other platforms see')
    def test_asking_for_the_win32_api_elsewhere_is_a_wgl_error(self):
        with pytest.raises(offscreen.WGLError) as raised:
            offscreen.win32()
        assert 'OpenGL.EGL' in str(raised.value)


@windows_only
class TestOffscreenRendering:
    """A real offscreen context, rendering a real frame.

    An exit status proves nothing here -- a context that creates cleanly and
    draws nothing exits zero -- so these read the pixels back.
    """

    @pytest.fixture
    def context(self):
        missing = offscreen.available()
        if missing:
            pytest.skip('no offscreen WGL here: %s missing' % (', '.join(missing),))
        context = offscreen.OffscreenContext(width=64, height=48)
        try:
            yield context
        finally:
            context.release()

    def test_the_frame_holds_what_was_drawn(self, context):
        """The whole point: a pbuffer is the default framebuffer, so an
        ordinary clear and an ordinary readback are all this takes."""
        import numpy as np
        from OpenGL import GL

        GL.glViewport(0, 0, 64, 48)
        GL.glClearColor(0.25, 0.50, 0.75, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        raw = GL.glReadPixels(0, 0, 64, 48, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
        pixels = np.frombuffer(bytes(raw), dtype=np.uint8).reshape(48, 64, 3)
        # Every pixel, not just one: a clear that only touched a corner would
        # otherwise read as a success.
        for channel, wanted in enumerate((0.25, 0.50, 0.75)):
            assert abs(float(pixels[..., channel].mean()) / 255 - wanted) < 0.02

    def test_it_is_the_profile_that_was_asked_for(self, context):
        from OpenGL import GL
        from OpenGL.WGL.ARB import create_context_profile

        assert GL.glGetIntegerv(GL.GL_CONTEXT_PROFILE_MASK) == (
            create_context_profile.WGL_CONTEXT_CORE_PROFILE_BIT_ARB)

    def test_it_is_the_version_that_was_asked_for(self, context):
        from OpenGL import GL

        assert (int(GL.glGetIntegerv(GL.GL_MAJOR_VERSION)),
                int(GL.glGetIntegerv(GL.GL_MINOR_VERSION))) >= (3, 3)

    def test_nothing_has_been_lost(self, context):
        assert context.lost is False

    def test_closing_twice_is_harmless(self, context):
        context.release()
        context.release()

    def test_it_works_as_a_context_manager(self):
        if offscreen.available():
            pytest.skip('no offscreen WGL here')
        with offscreen.headless_context(16, 16) as context:
            assert context.context
        assert context.context is None


@windows_only
class TestResizing:
    """A pbuffer is made at a fixed size, so resizing replaces it.

    Reading pixels back at the new size is what shows the surface really
    changed rather than only the viewport.
    """

    @pytest.fixture
    def context(self):
        if offscreen.available():
            pytest.skip('no offscreen WGL here')
        context = offscreen.OffscreenContext(width=32, height=32)
        try:
            yield context
        finally:
            context.release()

    def test_the_frame_comes_back_at_the_new_size(self, context):
        import numpy as np
        from OpenGL import GL

        context.resize(48, 24)
        GL.glViewport(0, 0, 48, 24)
        GL.glClearColor(0.0, 1.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        raw = GL.glReadPixels(0, 0, 48, 24, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
        pixels = np.frombuffer(bytes(raw), dtype=np.uint8).reshape(24, 48, 3)
        assert float(pixels[..., 1].mean()) > 200      # green, everywhere

    def test_the_recorded_size_follows(self, context):
        context.resize(48, 24)
        assert (context.width, context.height) == (48, 24)

    def test_what_the_context_held_survives(self, context):
        """The context is kept and rebound, so its objects are still there --
        which is what makes a resize cheaper than a rebuild."""
        from OpenGL import GL

        texture = int(GL.glGenTextures(1))
        # Bound, not merely generated: a name glGenTextures handed out is not
        # the name of a texture until glBindTexture has made one of it.
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        context.resize(48, 24)
        assert GL.glIsTexture(texture)
        GL.glDeleteTextures(1, [texture])

    def test_resizing_to_the_same_size_keeps_the_pbuffer(self, context):
        was = context.handle
        context.resize(32, 32)
        assert context.handle == was

    @pytest.mark.parametrize('size', [(0, 0), (0, 100), (100, 0),
                                      (-1, 100), (100, -1)])
    def test_a_degenerate_size_is_refused(self, context, size):
        """Every one of them: ``(width, height) <= (0, 0)`` is lexicographic
        ordering on tuples, which lets 100x0 and 100x-1 straight through."""
        with pytest.raises(offscreen.WGLError) as raised:
            context.resize(*size)
        assert 'cannot render at' in str(raised.value)


@windows_only
class TestTheBootstrap:
    """The hidden window the extension entry points are resolved through."""

    def test_it_is_shared_rather_than_made_per_context(self):
        assert offscreen.bootstrap() is offscreen.bootstrap()

    def test_it_rebuilds_after_being_released(self):
        was = offscreen.bootstrap()
        offscreen.release_bootstrap()
        assert offscreen.bootstrap() is not was

    def test_a_context_already_made_survives_the_bootstrap_going(self):
        """A pbuffer is not tied to the window it was created through, which
        is the reason the window can be a detail rather than a lifetime."""
        from OpenGL import GL

        if offscreen.available():
            pytest.skip('no offscreen WGL here')
        context = offscreen.OffscreenContext(width=16, height=16)
        try:
            offscreen.release_bootstrap()
            context.make_current()
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            assert context.lost is False
        finally:
            context.release()

    def test_it_puts_back_whatever_was_current(self):
        """An application that already had a context of its own must not find
        it quietly replaced by the one used to resolve an entry point."""
        from OpenGL import WGL

        if offscreen.available():
            pytest.skip('no offscreen WGL here')
        context = offscreen.OffscreenContext(width=16, height=16)
        try:
            mine = WGL.wglGetCurrentContext()
            offscreen.wgl_extensions()
            assert WGL.wglGetCurrentContext() == mine
        finally:
            context.release()

    def test_it_reports_the_extensions_the_driver_offers(self):
        offered = offscreen.wgl_extensions()
        assert isinstance(offered, frozenset)
        if offered:
            assert all(name.startswith('WGL_') for name in offered)


@windows_only
class TestSayingWhetherItCanRunAtAll:
    """``available`` answers before anything is created, which is what lets an
    application choose between this and a window."""

    def test_it_names_what_is_missing(self, monkeypatch):
        monkeypatch.setattr(offscreen, 'wgl_extensions',
                            lambda: frozenset(['WGL_ARB_pbuffer']))
        missing = offscreen.available()
        assert 'WGL_ARB_pixel_format' in missing
        assert 'WGL_ARB_pbuffer' not in missing

    def test_a_profile_needs_the_profile_extension(self, monkeypatch):
        monkeypatch.setattr(
            offscreen, 'wgl_extensions',
            lambda: frozenset(offscreen.REQUIRED_EXTENSIONS))
        assert offscreen.available('core') == (offscreen.PROFILE_EXTENSION,)
        assert offscreen.available('legacy') == ()

    def test_a_driver_that_cannot_be_asked_is_missing_everything(self, monkeypatch):
        def refuses():
            raise offscreen.WGLError('no window station here')

        monkeypatch.setattr(offscreen, 'wgl_extensions', refuses)
        assert offscreen.available() == offscreen.REQUIRED_EXTENSIONS

    def test_a_context_refuses_by_name_where_it_cannot_be_served(self, monkeypatch):
        monkeypatch.setattr(offscreen, 'available',
                            lambda profile='core': ('WGL_ARB_pbuffer',))
        with pytest.raises(offscreen.WGLError) as raised:
            offscreen.OffscreenContext(width=16, height=16)
        assert 'WGL_ARB_pbuffer' in str(raised.value)

    @pytest.mark.parametrize('size', [(0, 16), (16, 0), (-1, -1), (0.5, 16)])
    def test_a_degenerate_size_is_refused_before_anything_is_created(self, size):
        """``0.5`` among them: a fraction passes a ``> 0`` test and then rounds
        to a pbuffer no pixels wide, so the rounding comes first."""
        with pytest.raises(offscreen.WGLError) as raised:
            offscreen.OffscreenContext(width=size[0], height=size[1])
        assert 'cannot render at' in str(raised.value)
