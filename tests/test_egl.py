#! /usr/bin/env python
import OpenGL,ctypes
OpenGL.USE_ACCELERATE = False
from OpenGL import egl

def main():
    major,minor = ctypes.c_long(),ctypes.c_long()
    display = egl.eglGetDisplay(egl.EGL_DEFAULT_DISPLAY)
    #display = ctypes.c_voidp( display )
    print 'wrapped', display
    if not egl.eglInitialize( display, major, minor):
        print 'Unable to initialize'
    print 'EGL version %s.%s'%(major.value,minor.value)
    
    num_configs = ctypes.c_long()
    egl.eglGetConfigs(display, None, 0, num_configs)
    print '%s configs'%(num_configs.value)
   

if __name__ == "__main__":
    main()
