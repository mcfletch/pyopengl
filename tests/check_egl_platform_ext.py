"""This checking script from https://github.com/mcfletch/pyopengl/issues/6"""
import OpenGL
import OpenGL.platform.egl
OpenGL.platform.PLATFORM = p = OpenGL.platform.egl.EGLPlatform()
from OpenGL import EGL
from OpenGL.EGL.VERSION import EGL_1_5
from OpenGL.EGL.EXT import platform_base
from OpenGL.EGL.MESA import platform_gbm
import ctypes, glob

def main():
    cards = sorted(glob.glob("/dev/dri/renderD*"))
    if not cards:
        raise RuntimeError("Need a /dev/dri/renderD* device to do rendering")
    if len(cards) > 1:
        print("Note, using first card: %s"%(cards[0]))
    with open(cards[0], "w") as f:
        gbm = ctypes.CDLL("libgbm.so.1") # On Ubuntu, package libgbm1
        dev = gbm.gbm_create_device(f.fileno())
        dpy = platform_base.eglGetPlatformDisplayEXT(
            platform_gbm.EGL_PLATFORM_GBM_MESA, 
            ctypes.c_void_p(dev), 
            ctypes.c_void_p(0)
        )
        print(dpy)
        if EGL_1_5.eglGetPlatformDisplay:
            dpy = platform_base.eglGetPlatformDisplay(
                platform_gbm.EGL_PLATFORM_GBM_MESA, 
                ctypes.c_void_p(dev), 
                ctypes.c_void_p(0)
            )
            print(dpy)
        else:
            print("No EGL_1_5 implementation")

if __name__ == "__main__":
    main()
