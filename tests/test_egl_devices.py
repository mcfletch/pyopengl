"""What ``OpenGL.EGL.devices`` reports about the EGL devices present.

The classification is pure -- a device is described by the extensions it
advertises and the name its driver gives itself -- so most of this runs with no
EGL implementation to hand.  The enumeration cases need one and skip without it.
"""

import ctypes
import os

import pytest

from OpenGL.EGL import devices as devices_module
from OpenGL.EGL.devices import DeviceInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


class TestADeviceIsIdentifiedByItsHandle:
    """``index`` is a property of one enumeration and ``handle`` is the device.
    Comparing on the first and not the second says two different devices are
    the same when their drivers are, and that the same device re-enumerated at
    a different index is a different one."""

    def _device(self, index, address, driver='nvidia'):
        from OpenGL.EGL.devices import DeviceInfo

        return DeviceInfo(
            index=index,
            handle=ctypes.c_void_p(address),
            extensions=('EGL_EXT_device_drm',),
            driver=driver,
        )

    def test_two_devices_with_one_driver_are_not_equal(self):
        assert self._device(0, 0x1000) != self._device(1, 0x2000)

    def test_the_same_device_at_another_index_is_the_same_device(self):
        assert self._device(0, 0x1000) == self._device(1, 0x1000)

    def test_equal_devices_hash_alike(self):
        assert hash(self._device(0, 0x1000)) == hash(self._device(1, 0x1000))
        assert len({self._device(0, 0x1000), self._device(1, 0x1000)}) == 1

    def test_a_different_device_is_a_different_key(self):
        assert len({self._device(0, 0x1000), self._device(0, 0x2000)}) == 2


class TestAFailedQueryLeavesNoErrorBehind:
    """``_device_string`` expects a device that does not implement the query,
    so it swallows the failure -- but EGL records an error code that the next
    ``eglGetError`` any caller makes would read as its own."""

    def test_it_clears_the_egl_error_it_caused(self, monkeypatch):
        from OpenGL.EGL import devices

        cleared = []

        def refuses(handle, token):
            raise RuntimeError('no such query')

        monkeypatch.setattr(devices, 'eglQueryDeviceStringEXT', refuses)
        monkeypatch.setattr(
            devices, 'eglGetError', lambda: cleared.append(True) or 0x3000
        )
        assert devices._device_string(object(), 0x3055) == ''
        assert cleared == [True]


class TestTheModuleIsDocumented:
    """A public module nobody can find is a module nobody uses."""

    def test_there_is_a_page_for_it(self):
        page = os.path.join(ROOT, 'documentation', 'egl-devices.html')
        assert os.path.exists(page), page
        text = open(page, encoding='utf-8').read()
        for named in (
            'OpenGL.EGL.devices',
            'DeviceInfo',
            'software',
            'eglGetPlatformDisplayEXT',
            'EGL_PLATFORM_DEVICE_EXT',
        ):
            assert named in text, named

    def test_the_package_offers_it_without_a_deeper_import(self):
        from OpenGL import EGL

        assert EGL.devices is not None
        assert callable(EGL.devices.devices)
