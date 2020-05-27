#! /usr/bin/env python
import logging
import os_egl
from OpenGL.EGL import *
from OpenGL.EGL.EXT.device_enumeration import eglQueryDevicesEXT
log = logging.getLogger(__name__)

def main():
    devices = (EGLDeviceEXT * 10)()
    count = EGLint()
    major, minor = EGLint(), EGLint()
    if eglQueryDevicesEXT(10,devices,count):
        log.info("%s devices enumerated", count)
        for i,device in enumerate(devices[:count.value]):
            display = eglGetDisplay(device)
            if not eglInitialize(display,major,minor):
                log.info("Could not initialise, skipping")
                continue
            log.info("Display #%d, Version %s.%s",i,major.value,minor.value)
            for key in [
                EGL_VENDOR,
            ]:
                log.info("#%d %s", i, eglQueryString(display,key))
#        display = eglGetDisplay(EGL_DEFAULT_DISPLAY)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
