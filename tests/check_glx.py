from __future__ import print_function
#import OpenGL
#OpenGL.USE_ACCELERATE=False
from OpenGL.GL import *
from OpenGL.GLX import *
from OpenGL.GLX.EXT.texture_from_pixmap import *
from pygamegltest import pygametest
import os

print('Not yet working')
raise SystemExit(1)
attributes = [
#    GLX_BIND_TO_TEXTURE_RGBA_EXT, 1,
#    GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
#    GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
    GLX_DOUBLEBUFFER, 0,
#    GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
    GL_NONE
]
attributes = (GLint * len(attributes))( * attributes )

import ctypes
from OpenGL.platform import ctypesloader

X11 = ctypesloader.loadLibrary( ctypes.cdll, 'X11' )

XDefaultScreen = X11.XDefaultScreen
XDefaultScreen.argtypes = [ctypes.POINTER(Display)]

XOpenDisplay = X11.XOpenDisplay 
XOpenDisplay.restype = ctypes.POINTER(Display)

XRootWindow = X11.XRootWindow
XRootWindow.restyle = ctypes.POINTER( Window )

XCreateWindow = X11.XCreateWindow
XCreateWindow.restyle = ctypes.POINTER( Window )
XCreateWindow.argtypes = [
    ctypes.POINTER(Display),ctypes.POINTER(Window),
    GLint,GLint,GLuint,GLuint,GLuint,GLint,GLuint,
    ctypes.POINTER(Visual),
    ctypes.c_ulong,ctypes.c_void_p,
]
AllocNone = 0

#@pygametest()
def main():
    display = XOpenDisplay( os.environ.get( 'DISPLAY' ))
    screen = XDefaultScreen( display )
    print('X Display %s Screen %s'%( display, screen ))
    major,minor = GLint(),GLint()
    glXQueryVersion(display, major, minor)
    version = (major.value,minor.value)
    print('glX Version: %s.%s'%version)
    
    # get a visual with 1.0 functionality...
    vis = glXChooseVisual(display, screen, attributes)
    
    root = XRootWindow(display,vis.screen)
    window = XCreateWindow( 
        display, root, 
        0,0, #x,y
        300,300, #w,h,
        1, # border width
        vis.depth,
        1, # InputOutput Class
        vis.visual,
        0,
        ctypes.c_void_p(0),
    )
        
    context = glXCreateContext(display,visual,0,GL_TRUE)
    
    if version >= (1,1):
        print(glXQueryExtensionsString(display,screen))
#        if version >= (1,2):
#            d = glXGetCurrentDisplay()[0]
#            print 'Current display', d
#        else:
    
    
    
    if version >= (1,3):
        elements = GLint(0)
        configs = glXChooseFBConfig(
            display, 
            screen, 
            attributes, 
            elements
        )
        print('%s configs found'%( elements.value ))
        for config in range( elements.value ):
            print('Config: %s %s'%(config,configs[config][0]))
            samples = ctypes.c_int()
            for attribute in (
                'GLX_FBCONFIG_ID','GLX_BUFFER_SIZE',
                'GLX_LEVEL','GLX_DOUBLEBUFFER',
                'GLX_STEREO',
                'GLX_SAMPLES','GLX_SAMPLE_BUFFERS',
                'GLX_DRAWABLE_TYPE',
            ):
                glXGetFBConfigAttrib( display, configs[config], globals()[attribute], samples )
                print('%s -> %s'%( attribute, samples.value ))
            print() 
    
        
if __name__ == "__main__":
    main()
