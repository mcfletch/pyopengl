"""Which EGL device the headless test backend renders on.

The choice is policy over the facts :mod:`OpenGL.EGL.devices` reports, so it is
pure and runs with no EGL implementation present.

One combination is not merely a poor choice but a crash: Mesa refuses to force
software rendering onto a display that was created on a *hardware* device
(``EGL_PLATFORM_DEVICE_EXT``), and having said so it dereferences the screen it
declined to build -- ``eglInitialize`` segfaults inside ``driCreateNewScreen3``
rather than returning ``EGL_FALSE``.  Asking for software rendering must
therefore select a software device, and where there is none the backend says so
instead of handing back a device that would take the process down.
"""

import glcontext_egl
import pytest

from OpenGL.EGL.devices import DeviceInfo


def device(index, software=False, driver='radeonsi'):
    return DeviceInfo(
        index=index,
        handle=object(),
        extensions=('EGL_MESA_device_software',) if software else ('EGL_EXT_device_drm',),
        driver='llvmpipe' if software else driver,
    )


HARDWARE = device(0)
SOFTWARE = device(1, software=True)


class TestWhetherSoftwareRenderingWasAskedFor:
    """``LIBGL_ALWAYS_SOFTWARE`` as Mesa itself reads it: an unset variable and
    an empty one mean the same thing, and so do the spellings of "no".  Named
    and read the same way as OpenGLContext's offscreen backend, since a
    developer moves between the two and they answer about the same Mesa."""

    @pytest.mark.parametrize('value', ['1', 'yes', 'true', 'on'])
    def test_a_truthy_value_asks_for_it(self, value):
        assert glcontext_egl.software_forced({'LIBGL_ALWAYS_SOFTWARE': value})

    @pytest.mark.parametrize('value', ['', '0', 'false', 'no', 'n', 'f'])
    def test_these_do_not(self, value):
        assert not glcontext_egl.software_forced({'LIBGL_ALWAYS_SOFTWARE': value})

    def test_nor_does_an_unset_variable(self):
        assert not glcontext_egl.software_forced({})

    def test_the_value_is_read_case_insensitively(self):
        assert not glcontext_egl.software_forced({'LIBGL_ALWAYS_SOFTWARE': 'FALSE'})

    @pytest.mark.parametrize('name', ['llvmpipe', 'softpipe', 'swrast', 'swr',
                                      'lavapipe'])
    def test_a_software_gallium_driver_asks_for_it_too(self, name):
        """Naming a CPU rasteriser is asking for one.  It does not reach the
        device path by itself -- a display on a GPU device stays on the GPU
        whatever GALLIUM_DRIVER says -- so a run that pinned llvmpipe this way
        and got the GPU would be measuring something it did not ask for."""
        assert glcontext_egl.software_forced({'GALLIUM_DRIVER': name})

    def test_a_hardware_gallium_driver_does_not(self):
        assert not glcontext_egl.software_forced({'GALLIUM_DRIVER': 'radeonsi'})


class TestChoosingADevice:
    def test_a_gpu_is_preferred_when_nothing_says_otherwise(self):
        assert glcontext_egl.pick_device([SOFTWARE, HARDWARE], {}) is HARDWARE

    def test_the_software_device_serves_where_it_is_the_only_one(self):
        """A CI runner with no GPU: rendering in software is the whole offer."""
        assert glcontext_egl.pick_device([SOFTWARE], {}) is SOFTWARE

    def test_asking_for_software_selects_the_software_device(self):
        """The crashing combination, and the reason this function exists."""
        env = {'LIBGL_ALWAYS_SOFTWARE': '1'}
        assert glcontext_egl.pick_device([HARDWARE, SOFTWARE], env) is SOFTWARE

    def test_asking_for_software_with_no_software_device_is_refused(self):
        env = {'LIBGL_ALWAYS_SOFTWARE': '1'}
        with pytest.raises(glcontext_egl.NoSuitableDevice) as raised:
            glcontext_egl.pick_device([HARDWARE], env)
        assert 'LIBGL_ALWAYS_SOFTWARE' in str(raised.value)

    def test_no_devices_at_all_is_refused(self):
        with pytest.raises(glcontext_egl.NoSuitableDevice):
            glcontext_egl.pick_device([], {})


class TestPinningADevice:
    def test_an_index_selects_that_device(self):
        env = {'TEST_EGL_DEVICE': '1'}
        assert glcontext_egl.pick_device([HARDWARE, SOFTWARE], env) is SOFTWARE

    def test_an_index_past_the_end_is_refused_by_name(self):
        env = {'TEST_EGL_DEVICE': '7'}
        with pytest.raises(glcontext_egl.NoSuitableDevice) as raised:
            glcontext_egl.pick_device([HARDWARE], env)
        assert 'TEST_EGL_DEVICE' in str(raised.value)

    def test_pinning_a_gpu_while_forcing_software_is_refused(self):
        """Explicit or not, this is the combination that segfaults; the caller is
        told which of the two settings to drop rather than losing the process."""
        env = {'TEST_EGL_DEVICE': '0', 'LIBGL_ALWAYS_SOFTWARE': '1'}
        with pytest.raises(glcontext_egl.NoSuitableDevice) as raised:
            glcontext_egl.pick_device([HARDWARE, SOFTWARE], env)
        message = str(raised.value)
        assert 'TEST_EGL_DEVICE' in message and 'LIBGL_ALWAYS_SOFTWARE' in message

    def test_pinning_the_software_device_while_forcing_software_is_fine(self):
        env = {'TEST_EGL_DEVICE': '1', 'LIBGL_ALWAYS_SOFTWARE': '1'}
        assert glcontext_egl.pick_device([HARDWARE, SOFTWARE], env) is SOFTWARE
