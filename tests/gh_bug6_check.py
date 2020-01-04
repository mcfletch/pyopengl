#! /usr/bin/env python3
import os, logging, glob, ctypes
os.environ['PYOPENGL_PLATFORM'] = 'egl'
log = logging.getLogger(__name__)
import OpenGL
from OpenGL.EGL import gbmdevice
from OpenGL.EGL import *
from OpenGL.EGL.EXT.platform_base import *
from OpenGL.EGL.MESA.platform_gbm import *

def main():
    for device in gbmdevice.enumerate_devices():
        log.info("Checking device: %s", device)
        device = gbmdevice.open_device(device)
        try:
            display = eglGetPlatformDisplayEXT(
                EGL_PLATFORM_GBM_MESA, 
                device, 
                ctypes.c_void_p(0)
            )
            if display == EGL_NO_DISPLAY:
                log.error("Failed to get platform display for %s", display)
            else:
                log.info("Got platform display %s", display)
        finally:
            gbmdevice.close_device(device)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
