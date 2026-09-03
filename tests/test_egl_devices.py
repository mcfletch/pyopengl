"""What ``OpenGL.EGL.devices`` reports about the EGL devices present.

The classification is pure -- a device is described by the extensions it
advertises and the name its driver gives itself -- so most of this runs with no
EGL implementation to hand.  The enumeration cases need one and skip without it.
"""

import pytest

from OpenGL.EGL import devices as devices_module
from OpenGL.EGL.devices import DeviceInfo


def info(**overrides):
    """A DeviceInfo with uninteresting values for everything not under test."""
    fields = {
        'index': 0,
        'handle': None,
        'extensions': ('EGL_EXT_device_drm',),
        'driver': 'radeonsi',
    }
    fields.update(overrides)
    return DeviceInfo(**fields)


class TestSoftwareClassification:
    def test_hardware_device_is_not_software(self):
        assert not info().software

    def test_the_mesa_extension_marks_a_software_device(self):
        """A Mesa software device says so outright; that is the reliable signal."""
        assert info(extensions=('EGL_MESA_device_software',), driver='').software

    def test_a_software_driver_name_marks_one_too(self):
        """Not every implementation advertises the extension, but names are telling."""
        assert info(extensions=(), driver='llvmpipe').software

    def test_driver_names_match_case_insensitively(self):
        assert info(extensions=(), driver='LLVMpipe (LLVM 20.1.2)').software

    @pytest.mark.parametrize('name', ['swrast', 'softpipe', 'swr', 'lavapipe'])
    def test_the_other_software_drivers(self, name):
        assert info(extensions=(), driver=name).software

    def test_an_unidentifiable_device_is_not_called_software(self):
        """With nothing to go on, saying 'hardware' is the safer report."""
        assert not info(extensions=(), driver='').software

    def test_a_hardware_driver_named_after_a_vendor_is_not_software(self):
        assert not info(extensions=('EGL_EXT_device_drm',), driver='iris').software


class TestDeviceInfo:
    def test_repr_identifies_the_device(self):
        text = repr(info(index=2, driver='radeonsi'))
        assert '2' in text and 'radeonsi' in text

    def test_repr_says_when_a_device_is_software(self):
        assert 'software' in repr(info(extensions=('EGL_MESA_device_software',))).lower()

    def test_is_hashable(self):
        assert {info(), info()}


@pytest.fixture(scope='module')
def found():
    """The devices this system actually reports."""
    try:
        found = devices_module.devices()
    except Exception as error:  # noqa: BLE001 - no EGL, or no enumeration extension
        pytest.skip(f'EGL device enumeration unavailable: {error}')
    if not found:
        pytest.skip('no EGL devices on this system')
    return found


class TestEnumeration:
    """These need a working EGL; they describe shape, not which devices exist."""

    def test_devices_are_indexed_in_order(self, found):
        assert [device.index for device in found] == list(range(len(found)))

    def test_every_device_reports_its_extensions_as_a_tuple(self, found):
        for device in found:
            assert isinstance(device.extensions, tuple)

    def test_every_device_keeps_its_handle(self, found):
        """The handle is what a caller passes to eglGetPlatformDisplayEXT."""
        for device in found:
            assert device.handle is not None

    def test_software_is_answerable_for_every_device(self, found):
        for device in found:
            assert device.software in (True, False)

    def test_enumeration_without_the_extension_reports_nothing(self):
        """A system with no device enumeration has no devices to report, not an error."""
        assert devices_module.devices(query=lambda: None) == ()
