#! /usr/bin/env python
import logging

# import os_egl
from OpenGL.EGL import *
from OpenGL.EGL.EXT.device_enumeration import eglQueryDevicesEXT

log = logging.getLogger(__name__)


def main():
    devices = (EGLDeviceEXT * 10)()
    count = EGLint()
    major, minor = EGLint(), EGLint()
    if not eglQueryDevicesEXT:
        raise RuntimeError("No egl query devices extension available")
    if eglQueryDevicesEXT(10, devices, count):
        log.info("%s devices enumerated", count)
        for i, device in enumerate(devices[: count.value]):
            log.info("Describing device #%d: %s", i, device)
            display = eglGetDisplay(device)
            try:
                if not eglInitialize(display, major, minor):
                    log.info("Could not initialise, skipping")
                    continue
            except EGLError as err:
                log.warning("Unable to initialise EGL for display %d: %s", i, err)
            log.info("Display #%d, Version %s.%s", i, major.value, minor.value)
            for key in [
                EGL_VENDOR,
            ]:
                log.info(" Vendor: %s", eglQueryString(display, key))
            log.info("Finished device #%d", i)
    else:
        log.warning("Unable to query devices")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
