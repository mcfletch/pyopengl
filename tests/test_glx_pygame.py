from __future__ import print_function
#import OpenGL
#OpenGL.USE_ACCELERATE=False
from OpenGL.GL import *
import pytest
import sys
if not sys.platform.startswith('linux'):
    pytest.skip("Skipping GLX tests on non-linux platforms", allow_module_level=True)
from OpenGL.GLX import *
from OpenGL.GLX.EXT.texture_from_pixmap import *
from pygamegltest import pygametest
import os

attributes = [
#    GLX_BIND_TO_TEXTURE_RGBA_EXT, 1,
#    GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
#    GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
    GLX_DOUBLEBUFFER, 1,
#    GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
    GL_NONE
]

#from OpenGL import platform
import ctypes
from OpenGL.platform import ctypesloader

X11 = ctypesloader.loadLibrary( ctypes.cdll, 'X11' )
XDefaultScreen = X11.XDefaultScreen
XDefaultScreen.argtypes = [ctypes.POINTER(Display)]
XOpenDisplay = X11.XOpenDisplay 
XOpenDisplay.restype = ctypes.POINTER(Display)

@pygametest()
def main():
    dsp = XOpenDisplay( os.environ.get( 'DISPLAY' ))
    screen = XDefaultScreen( dsp )
    print('X Display %s Screen %s'%( dsp, screen ))
    major,minor = GLint(),GLint()
    glXQueryVersion(dsp, major, minor)
    version = (major.value,minor.value)
    print('glX Version: %s.%s'%version)
    if version >= (1,1):
        print(glXQueryExtensionsString(dsp,screen))
        if version >= (1,2):
            d = glXGetCurrentDisplay()[0]
            print('Current display', d)
        else:
            d = dsp
    if version >= (1,3):
        elements = GLint(0)
        configs = glXChooseFBConfig(
            dsp, 
            screen, 
            (GLint * len(attributes))( * attributes ), 
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
                glXGetFBConfigAttrib( dsp, configs[config], globals()[attribute], samples )
                print('%s -> %s'%( attribute, samples.value ))
            print() 
    from OpenGL.raw.GLX import _types
    print('Extension List', _types.GLXQuerier.getExtensions())
        
if __name__ == "__main__":
    main()
