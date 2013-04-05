#! /usr/bin/env python
"""Implements the functionality in MESA's EGL + OpenGL demo1:

    http://cgit.freedesktop.org/mesa/demos/tree/src/egl/opengl/demo1.c

Basically just to check if the EGL code works...
"""
import OpenGL,ctypes
OpenGL.USE_ACCELERATE = False
from OpenGL.egl import *

def describe_config( display, config ):
    """Describe the given configuration"""
    parameters = (EGL_CONFIG_ID,
        EGL_BUFFER_SIZE,
        EGL_LEVEL,
        EGL_RED_SIZE,
        EGL_GREEN_SIZE,
        EGL_BLUE_SIZE,
        EGL_ALPHA_SIZE,
        EGL_DEPTH_SIZE,
        EGL_STENCIL_SIZE,
        EGL_SURFACE_TYPE)
    description = []
    for param in parameters:
        value = ctypes.c_long()
        eglGetConfigAttrib(display, config, param, value)
        description.append( '%s = %s'%( param, value.value, ))
    return '\n'.join( description )

def main():
    major,minor = ctypes.c_long(),ctypes.c_long()
    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    print 'Display return value', display 
    print 'Display address', display.address
    #display = display.as_voidp
    #print 'wrapped', display
    if not eglInitialize( display, major, minor):
        print 'Unable to initialize'
    print 'EGL version %s.%s'%(major.value,minor.value)
    
    num_configs = ctypes.c_long()
    eglGetConfigs(display, None, 0, num_configs)
    print '%s configs'%(num_configs.value)
    
    configs = (EGLConfig * num_configs.value)()
    eglGetConfigs(display,configs,num_configs.value,num_configs)
    for config_id in configs:
        #print config_id
        describe_config( display, config_id )
    
    print 'Attempting to bind and create contexts/apis'
    eglBindAPI(EGL_OPENGL_API)
    ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
    if ctx == EGL_NO_CONTEXT:
        print 'Unable to create the regular context'
    else:
        print 'Created regular context'
    
    pbufAttribs = (EGLint * 5)(* [EGL_WIDTH,500, EGL_HEIGHT, 500, EGL_NONE])
    pbuffer = eglCreatePbufferSurface(display, configs[0], pbufAttribs);
    if (pbuffer == EGL_NO_SURFACE):
        print 'Unable to create pbuffer surface'
    else:
        print 'created pbuffer surface'

if __name__ == "__main__":
    main()
