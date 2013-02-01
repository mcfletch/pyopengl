#! /usr/bin/env python
import OpenGL 
OpenGL.USE_ACCELERATE = False
from OpenGL import egl

def main():
   display = egl.eglGetDisplay(egl.EGL_DEFAULT_DISPLAY)
   print 'wrapped', display
   display = egl._p.EGL.eglGetDisplay(egl.EGL_DEFAULT_DISPLAY)
   print 'with raw',display

if __name__ == "__main__":
    main()
