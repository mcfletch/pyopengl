#! /usr/bin/env python
"""What EGL devices this machine offers, and what each one initialises to.

Run it to find out whether headless EGL rendering is possible here and on which
device -- the first thing to ask when the suite's ``TEST_WINDOWING=egl`` backend
finds nothing to render on::

    python tests/report_egl_device_enumeration.py

Each device is described from :mod:`OpenGL.EGL.devices`, which needs no display
and no initialisation.  Only then is a display opened on it, since that is the
step that costs something and the step that can fail.

``LIBGL_ALWAYS_SOFTWARE`` is honoured rather than ignored: Mesa will not force
software rasterisation onto a display built on a hardware device, and having
said so it dereferences the screen it declined to build -- ``eglInitialize``
takes the process down rather than returning ``EGL_FALSE``.  So a device that
setting rules out is described and left alone.
"""

import logging

from OpenGL.EGL import (
    EGL_NO_DISPLAY,
    EGL_VENDOR,
    EGL_VERSION,
    EGLint,
    EGLError,
    eglInitialize,
    eglQueryString,
)
from OpenGL.EGL.devices import devices
from OpenGL.EGL.EXT.platform_base import eglGetPlatformDisplayEXT
from OpenGL.EGL.EXT.platform_device import EGL_PLATFORM_DEVICE_EXT

from glcontext_egl import software_forced

log = logging.getLogger(__name__)


def describe(device):
    """Open a display on one device and report what it says it is."""
    display = eglGetPlatformDisplayEXT(EGL_PLATFORM_DEVICE_EXT, device.handle, None)
    if display == EGL_NO_DISPLAY:
        log.warning("  no display for this device")
        return
    major, minor = EGLint(), EGLint()
    try:
        if not eglInitialize(display, major, minor):
            log.warning("  will not initialise")
            return
    except EGLError as err:
        log.warning("  will not initialise: %s", err)
        return
    log.info("  EGL %s.%s", major.value, minor.value)
    for name, key in (('vendor', EGL_VENDOR), ('version', EGL_VERSION)):
        log.info("  %s: %s", name, eglQueryString(display, key))


def main():
    found = devices()
    if not found:
        log.warning(
            "No EGL devices: either EGL_EXT_device_enumeration is missing or "
            "there is nothing here to render on."
        )
        return
    software = software_forced()
    log.info("%d EGL device(s)", len(found))
    for device in found:
        log.info("%s", device)
        if software and not device.software:
            log.info("  skipped: LIBGL_ALWAYS_SOFTWARE rules this device out")
            continue
        describe(device)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
