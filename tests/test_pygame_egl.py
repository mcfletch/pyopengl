#! /usr/bin/env python
import pygame
import pygame.display
from OpenGL.egl import *
import ctypes
from OpenGL.platform import ctypesloader
X11 = ctypesloader.loadLibrary( ctypes.cdll, 'X11' )
XOpenDisplay = X11.XOpenDisplay
XOpenDisplay.restype = EGLNativeDisplayType

def init_default_display(info):
    major,minor = EGLint(),EGLint()
    x_display = XOpenDisplay( ':0' )
    if not x_display:
        raise RuntimeError("Null XOpenDisplay result")
    else:
        print 'X Display', x_display
    display = eglGetDisplay(x_display)
    if not display:
        raise RuntimeError( "Unable to retrive display" )
    else:
        print 'EGL Display', display
    if not eglInitialize( display, major, minor):
        raise RuntimeError( 'Unable to initialize' )
    return major.value, minor.value


def main(size=(300,300)):
    pygame.display.init()
    info = pygame.display.get_wm_info()
    hwnd = info['window']
    
    SCREEN = pygame.display.set_mode(
        size,
        pygame.HWSURFACE,
    )
    init_default_display(info)
    
if __name__ == "__main__":
    main()
    
