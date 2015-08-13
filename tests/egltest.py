"""EGL Pygame test framework"""
from __future__ import print_function
import ctypes
import pygame.display 
import pygame 
import os 
import logging
import OpenGL
from functools import wraps

if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'egl'
if os.environ.get( 'TEST_NO_ACCELERATE' ):
    OpenGL.USE_ACCELERATE = False

from OpenGL import arrays
from OpenGL.EGL import *
log = logging.getLogger( __name__ )

DESIRED_ATTRIBUTES = [
    EGL_BLUE_SIZE, 8,
    EGL_RED_SIZE,8,
    EGL_GREEN_SIZE,8,
    EGL_DEPTH_SIZE,24,
    EGL_COLOR_BUFFER_TYPE, EGL_RGB_BUFFER,
    EGL_CONFIG_CAVEAT, EGL_NONE, # Don't allow slow/non-conformant
]
API_BITS = {
    'opengl': EGL_OPENGL_BIT,
    'gl': EGL_OPENGL_BIT,
    'gles2': EGL_OPENGL_ES2_BIT,
    'gles1': EGL_OPENGL_ES_BIT,
    'gles': EGL_OPENGL_ES_BIT,
    'es2': EGL_OPENGL_ES2_BIT,
    'es1': EGL_OPENGL_ES_BIT,
    'es': EGL_OPENGL_ES_BIT,
}
API_NAMES = dict([
    (k,{
        EGL_OPENGL_BIT:EGL_OPENGL_API,
        EGL_OPENGL_ES2_BIT:EGL_OPENGL_ES_API,
        EGL_OPENGL_ES_BIT:EGL_OPENGL_ES_API
    }[v])
    for k,v in API_BITS.items()
])


def egltest( size=(300,300), name=None, api='es2', attributes=DESIRED_ATTRIBUTES ):
    def gltest( function ):
        """Decorator to allow a function to run in a Pygame GLES[1,2,3] context"""
        @wraps( function )
        def test_function( *args, **named ):
            major,minor = ctypes.c_long(),ctypes.c_long()
            display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
            eglInitialize( display, major, minor)
            num_configs = ctypes.c_long()
            configs = (EGLConfig*2)()
            api_constant = API_NAMES[api.lower()]
            local_attributes = attributes[:]
            local_attributes.extend( [
                EGL_CONFORMANT, API_BITS[api.lower()],
                EGL_NONE,
            ])
            print('local_attributes', local_attributes)
            local_attributes= arrays.GLintArray.asArray( local_attributes )
            eglChooseConfig(display, local_attributes, configs, 2, num_configs)
            print('API', api_constant)
            eglBindAPI(api_constant)
            
            # now need to get a raw X window handle...
            pygame.init()
            pygame.display.set_mode( size )
            window = pygame.display.get_wm_info()['window']
            surface = eglCreateWindowSurface(display, configs[0], window, None )
            
            ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
            if ctx == EGL_NO_CONTEXT:
                raise RuntimeError( 'Unable to create context' )
            try:
                eglMakeCurrent( display, surface, surface, ctx )
                function(*args, **named)
                eglSwapBuffers( display, surface )
            finally:
                pygame.display.quit()
                pygame.quit()
        return test_function
    return gltest 
