from __future__ import print_function
#import OpenGL
#OpenGL.USE_ACCELERATE=False
from OpenGL.GL import *
from OpenGL.GLX import *
from OpenGL.GLX.EXT.texture_from_pixmap import *
from pygamegltest import pygametest
import os

# print('Not yet working')
# raise SystemExit(1)
attributes = [
#    GLX_BIND_TO_TEXTURE_RGBA_EXT, 1,
#    GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
#    GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
    GLX_DRAWABLE_TYPE, GLX_WINDOW_BIT,
    GLX_RED_SIZE, 8,
    GLX_GREEN_SIZE, 8,
    GLX_BLUE_SIZE, 8,
    GLX_ALPHA_SIZE, 8,
    GLX_DEPTH_SIZE, 24,
    GLX_STENCIL_SIZE, 8,
    GLX_RENDER_TYPE, GLX_RGBA_BIT,
    GLX_X_VISUAL_TYPE , GLX_TRUE_COLOR,
    GLX_DOUBLEBUFFER, 1,
    GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
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
XFree = X11.XFree
AllocNone = 0
def debug_struct(s):
    return dict([
        (k, getattr(s,k,None))
        for k in s.__class__.__slots__
    ])

#@pygametest()
def main():
    display = XOpenDisplay( os.environ.get( 'DISPLAY' ))
    if not display:
        raise RuntimeError("Unable to get the default display")
    screen = XDefaultScreen( display )
    print('X Display %s Screen %s'%( display, screen ))
    major,minor = GLint(),GLint()
    glXQueryVersion(display, major, minor)
    version = (major.value,minor.value)
    print('glX Version: %s.%s'%version)
    if (major.value,minor.value) < (1,3):
        print("Need at least GLX 1.3 to choose the framebuffer config")
        raise RuntimeError((major.value,minor.value))

    # Get the framebuffer configuration...
    count = ctypes.c_int(0)
    configs = glXChooseFBConfig(display, screen, attributes, ctypes.pointer(count))
    if count.value < 1:
        raise RuntimeError('Did not find any configs')
    print('Found %s configs'%(count.value,))

    for index in range(count.value):
        vis = glXGetVisualFromFBConfig( display, configs[index] )
        if vis:
            vis = vis[0]
            print('Visual %s: %s'%(index+1, debug_struct(vis)))
    
    # get a visual with 1.0 functionality...
    if not vis:
        print("Did not get a double-buffering visual, somehow?")
        raise RuntimeError("No double-buffered visual available")
    
    root = XRootWindow(display,vis.screen)
    root_p = ctypes.c_ulong(root)
    window = XCreateWindow( 
        display, 
        root_p, 
        0,0, #x,y
        300,300, #w,h,
        1, # border width
        vis.depth,
        1, # InputOutput Class
        vis.visual,
        0,
        ctypes.c_void_p(0),
    )
        
    context = glXCreateContext(display,vis,None,GL_TRUE)
    
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
