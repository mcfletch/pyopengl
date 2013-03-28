#! /usr/bin/env python
import OpenGL,ctypes
OpenGL.USE_ACCELERATE = False
from OpenGL import egl

def describe_config( display, config ):
    """Describe the given configuration"""
    parameters = '''EGL_CONFIG_ID,
        EGL_BUFFER_SIZE,
        EGL_LEVEL,
        EGL_RED_SIZE,
        EGL_GREEN_SIZE,
        EGL_BLUE_SIZE,
        EGL_ALPHA_SIZE,
        EGL_DEPTH_SIZE,
        EGL_STENCIL_SIZE,
        EGL_SURFACE_TYPE'''.replace(',','').split()
    description = []
    for param in parameters:
        value = ctypes.c_long()
        
        egl.eglGetConfigAttrib(display, config, getattr(egl,param), value)
        description.append( '%s = %s'%( param, value.value, ))
    return '\n'.join( description )

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
    configs = (egl._cs.EGLConfig * num_configs.value)()
    egl.eglGetConfigs(display,configs,num_configs.value,num_configs)
    for config_id in configs:
        print config_id
        print describe_config( display, config_id )
    
   

if __name__ == "__main__":
    main()
