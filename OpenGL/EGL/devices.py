"""The EGL devices this system offers, and what each one is.

``EGL_EXT_device_enumeration`` lets a program render on a specific device
without a display server, which is how offscreen and headless rendering is done
on EGL.  Getting from "the extension exists" to "this handle is the one I want"
means three separate extensions and a pair of string queries, so this module
does that once.

What it reports is fact: which devices exist, which extensions each advertises,
what its driver calls itself, and whether it renders in software.  *Choosing*
between them is policy and belongs to the caller -- a renderer wanting speed and
a test wanting reproducibility disagree about which device is the right one.

    >>> from OpenGL.EGL import devices
    >>> for device in devices.devices():
    ...     print(device.index, device.driver, device.software)

Each :class:`DeviceInfo` keeps the handle it was built from, which is what
``eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)`` takes.
"""

import logging

from OpenGL.EGL import EGL_EXTENSIONS, EGLint
from OpenGL.EGL.EXT.device_base import EGLDeviceEXT, eglQueryDeviceStringEXT
from OpenGL.EGL.EXT.device_enumeration import eglQueryDevicesEXT
from OpenGL.EGL.EXT.device_persistent_id import EGL_DRIVER_NAME_EXT

log = logging.getLogger(__name__)

__all__ = (
    'SOFTWARE_DRIVER_NAMES',
    'SOFTWARE_EXTENSION',
    'DeviceInfo',
    'devices',
)

#: A Mesa device that rasterises on the CPU advertises this.  Where it is
#: present it is definitive, which is why it is checked before driver names.
SOFTWARE_EXTENSION = 'EGL_MESA_device_software'

#: Driver names that mean CPU rasterisation, for implementations that do not
#: advertise :data:`SOFTWARE_EXTENSION`.  Matched case-insensitively as
#: substrings, because drivers append versions and build details to the name.
SOFTWARE_DRIVER_NAMES = ('llvmpipe', 'swrast', 'softpipe', 'swr', 'lavapipe')


class DeviceInfo:
    """One EGL device, and what could be learned about it.

    ``handle`` is the ``EGLDeviceEXT`` itself; the rest is what the device
    answered when asked.  Either string query may return nothing -- they come
    from optional extensions -- so ``extensions`` can be empty and ``driver``
    can be ``''``.
    """

    __slots__ = ('driver', 'extensions', 'handle', 'index')

    def __init__(self, index, handle, extensions=(), driver=''):
        self.index = index
        self.handle = handle
        self.extensions = tuple(extensions)
        self.driver = driver or ''

    @property
    def software(self) -> bool:
        """Whether this device rasterises on the CPU.

        A device that cannot be identified is reported as hardware: that is the
        safer answer, since treating a real GPU as software costs performance
        while the reverse can mean selecting a device that cannot do the work.
        """
        if SOFTWARE_EXTENSION in self.extensions:
            return True
        driver = self.driver.lower()
        return any(name in driver for name in SOFTWARE_DRIVER_NAMES)

    def __repr__(self) -> str:
        kind = 'software' if self.software else 'hardware'
        driver = self.driver or '<unnamed driver>'
        return f'<{self.__class__.__name__} {self.index} {driver} ({kind})>'

    def __eq__(self, other):
        if not isinstance(other, DeviceInfo):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    def _key(self):
        return (self.index, self.extensions, self.driver)


def _device_string(handle, token) -> str:
    """One string query, or ``''`` when the device declines to answer.

    Both tokens come from optional extensions, so a device that does not
    implement them is expected rather than exceptional.
    """
    try:
        value = eglQueryDeviceStringEXT(handle, token)
    except Exception as error:  # noqa: BLE001 - any failure here means "no answer"
        log.debug('eglQueryDeviceStringEXT(%s) failed: %s', token, error)
        return ''
    if not value:
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return str(value)


def _query_handles():
    """Every ``EGLDeviceEXT`` this system reports, or ``None`` if it cannot say."""
    try:
        count = EGLint()
        if not eglQueryDevicesEXT(0, None, count):
            return None
        if count.value < 1:
            return []
        handles = (EGLDeviceEXT * count.value)()
        if not eglQueryDevicesEXT(count.value, handles, count):
            return None
        return [handles[index] for index in range(count.value)]
    except Exception as error:  # noqa: BLE001 - see below; any failure means "cannot say"
        # No EGL_EXT_device_enumeration here.  That is a fact about the system,
        # not a failure of the caller's, so it is reported as "cannot say".
        log.debug('eglQueryDevicesEXT unavailable: %s', error)
        return None


def devices(query=_query_handles) -> tuple:
    """Every EGL device on this system, in the order EGL reports them.

    Returns an empty tuple when the system cannot enumerate devices at all --
    no ``EGL_EXT_device_enumeration``, or no devices behind it.  A caller that
    needs a display in that case should fall back to ``eglGetDisplay`` with
    ``EGL_DEFAULT_DISPLAY``.

    ``query`` is the enumeration step, exposed so it can be replaced in tests.
    """
    handles = query()
    if not handles:
        return ()
    return tuple(
        DeviceInfo(
            index=index,
            handle=handle,
            extensions=tuple(_device_string(handle, EGL_EXTENSIONS).split()),
            driver=_device_string(handle, EGL_DRIVER_NAME_EXT),
        )
        for index, handle in enumerate(handles)
    )
