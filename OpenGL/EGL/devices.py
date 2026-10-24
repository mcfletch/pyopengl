"""The EGL devices this system offers, and what each one is.

``EGL_EXT_device_enumeration`` lets a program render on a specific device
without a display server.  EGL uses it for offscreen and headless rendering.
Identifying each device takes three extensions and two string queries, which
this module wraps.

The module lists the devices, the extensions each one advertises, its driver
name and whether it renders in software.  The caller chooses which device to
use.  For example, a renderer may prefer a GPU, and a test may prefer a
software renderer for reproducible output.

    >>> from OpenGL.EGL import devices
    >>> for device in devices.devices():
    ...     print(device.index, device.driver, device.software)

Each :class:`DeviceInfo` keeps its device handle, for use in
``eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, handle, None)``.
"""

import ctypes
import logging

from OpenGL.EGL import EGL_EXTENSIONS, EGLint, eglGetError
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

#: The extension a Mesa device that rasterises on the CPU advertises.  It is
#: checked before driver names because it is definitive.
SOFTWARE_EXTENSION = 'EGL_MESA_device_software'

#: Driver names that mean CPU rasterisation, for implementations that do not
#: advertise :data:`SOFTWARE_EXTENSION`.  Matched case-insensitively as
#: substrings, because drivers append versions and build details to the name.
SOFTWARE_DRIVER_NAMES = ('llvmpipe', 'swrast', 'softpipe', 'swr', 'lavapipe')


class DeviceInfo:
    """One EGL device and the properties its queries returned.

    ``handle`` is the ``EGLDeviceEXT``.  The other attributes come from string
    queries in optional extensions, which may return nothing.  ``extensions``
    can therefore be empty and ``driver`` can be ``''``.
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

        A device that cannot be identified is reported as hardware.  Treating a
        GPU as software costs performance.  Treating a software renderer as a
        GPU can select a device that cannot do the work, which is worse.
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
        """The handle's address, used for equality and hashing.

        Devices are compared by handle.  ``index`` belongs to one enumeration,
        and two enumerations may number the same devices differently.  The
        handle is an ``EGLDeviceEXT`` pointer, which is not hashable, so its
        address is used.
        """
        return _address_of(self.handle)


def _address_of(handle) -> int:
    """The address an ``EGLDeviceEXT`` holds, or 0 where there is none."""
    if handle is None:
        return 0
    try:
        return ctypes.cast(handle, ctypes.c_void_p).value or 0
    except (ctypes.ArgumentError, TypeError):
        return id(handle)


def _device_string(handle, token) -> str:
    """The result of one device string query, or ``''`` if it fails.

    Both tokens come from optional extensions, so a failed query is normal.
    The EGL error a failed query records is cleared.  EGL keeps one error per
    thread, and the caller's next ``eglGetError`` would otherwise return it.
    """
    try:
        value = eglQueryDeviceStringEXT(handle, token)
    except Exception as error:  # noqa: BLE001 - any failure here means "no answer"
        log.debug('eglQueryDeviceStringEXT(%s) failed: %s', token, error)
        _clear_egl_error()
        return ''
    if not value:
        _clear_egl_error()
        return ''
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return str(value)


def _clear_egl_error() -> None:
    """Read and discard the EGL error a query in this module recorded."""
    try:
        eglGetError()
    except Exception as error:  # noqa: BLE001 - no EGL to ask is not a failure
        log.debug('eglGetError unavailable: %s', error)


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
        # The system has no EGL_EXT_device_enumeration.  The caller did nothing
        # wrong, so this returns None and does not raise.
        log.debug('eglQueryDevicesEXT unavailable: %s', error)
        return None


def devices(query=_query_handles) -> tuple:
    """Every EGL device on this system, in the order EGL reports them.

    Returns an empty tuple when the system cannot enumerate devices.  That
    happens without ``EGL_EXT_device_enumeration``, or when it reports no
    devices.  A caller that needs a display should then use ``eglGetDisplay``
    with ``EGL_DEFAULT_DISPLAY``.

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
