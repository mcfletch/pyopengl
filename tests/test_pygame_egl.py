#! /usr/bin/env python
import pygame
import pygame.display
from OpenGL.egl import *

def init_default_display(info):
    major,minor = EGLint(),EGLint()
    import pdb
    pdb.set_trace()
    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    if not display:
        raise RuntimeError( "Unable to retrive display" )
    if not eglInitialize( display, major, minor):
        raise RuntimeError( 'Unable to initialize' )
    return major.value, minor.value


def main():
    pygame.display.init()
    info = pygame.display.get_wm_info()
    hwnd = info['window']
    
    init_default_display(info)
    
if __name__ == "__main__":
    main()
    
