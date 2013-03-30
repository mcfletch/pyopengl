#! /usr/bin/env python
import wx
from OpenGL.egl import *

class TestFrame( wx.Frame ):
    def __init__( self, *args, **named ):
        super( TestFrame, self ).__init__( *args, **named )
        
        major,minor = ctypes.c_long(),ctypes.c_long()
        display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
        if not display:
            raise RuntimeError( "Unable to retrive display" )
        print 'display', display
        if not eglInitialize( display, major, minor):
            print 'Unable to initialize'
        print 'EGL version %s.%s'%(major.value,minor.value)
    
        num_configs = ctypes.c_long()
        eglGetConfigs(display, None, 0, num_configs)
        configs = (EGLConfig * num_configs.value)()
        eglGetConfigs(display,configs,num_configs.value,num_configs)
        attribList = [
            EGL_ALPHA_SIZE,8,
            EGL_DEPTH_SIZE,8,
            EGL_RED_SIZE,8,
            EGL_GREEN_SIZE,8,
            EGL_BLUE_SIZE,8,
            EGL_NONE
        ]
        config = EGLConfig()
        eglChooseConfig(display, attribList, config, 1, num_configs)
        surface = eglCreateWindowSurface(display, config, self.GetHandle(), None)
        context = eglCreateContext(display, config, EGL_NO_CONTEXT, None )
        eglMakeCurrent(display, surface, surface, context)

        eglBindAPI(EGL_OPENGL_API)


class Application( wx.App ):
    """Our application"""
    def __init__( self, *args, **named ):
        super( Application, self ).__init__( *args, **named )
        frame = TestFrame( None )
        frame.Show(True)
        self.SetTopWindow(frame)

def main():
    app = Application()
    app.MainLoop()

if __name__ == "__main__":
    main()
    
