from __future__ import print_function
import os, logging
log = logging.getLogger( __name__ )
if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'egl'
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']
import logging, contextlib
from functools import wraps
from OpenGL.GL import *
from OpenGL.EGL import *
from OpenGL import arrays

API_MAP = {
    EGL_OPENGL_BIT:EGL_OPENGL_API,
    EGL_OPENGL_ES2_BIT:EGL_OPENGL_ES_API,
    EGL_OPENGL_ES_BIT:EGL_OPENGL_ES_API,
}

def write_ppm(buf, filename):
    f = open(filename, "w")
    if f:
        h, w, c = buf.shape
        print( "P3", file=f)
        print( "# ascii ppm file created by os_egl",file=f)
        print( "%i %i" % (w, h),file=f)
        print("255",file=f)
        for y in range(h - 1, -1, -1):
            for x in range(w):
                pixel = buf[y, x]
                l = " %3d %3d %3d" % (pixel[0], pixel[1], pixel[2])
                f.write(l)
            f.write("\n")


@contextlib.contextmanager
def egl_context(
    width=400,
    height=400, 
    api=EGL_OPENGL_BIT,
    attributes = (
        EGL_BLUE_SIZE, 8,
        EGL_RED_SIZE,8,
        EGL_GREEN_SIZE,8,
        EGL_DEPTH_SIZE,24,
        EGL_COLOR_BUFFER_TYPE, EGL_RGB_BUFFER,
        EGL_CONFIG_CAVEAT, EGL_NONE, # Don't allow slow/non-conformant
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
    ),
    output='output.ppm',
):
    """Setup a context for rendering"""
    major,minor = GLint(), GLint()
    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    if display == EGL_NO_DISPLAY:
        raise RuntimeError(EGL_NO_DISPLAY, )
    # print("Display: %s"%(display.address,))
    eglInitialize( display, major, minor)
    num_configs = GLint()
    configs = (EGLConfig*2)()
    local_attributes = list(attributes[:])
    local_attributes.extend( [
        # EGL_CONFORMANT, api,
        EGL_NONE, # end of list
    ])
    log.info("Attributes: %s", local_attributes)
    local_attributes= arrays.GLintArray.asArray( local_attributes )
    try:
        eglChooseConfig(display, local_attributes, configs, 2, num_configs)
        surface_attributes = [
            EGL_WIDTH,width,
            EGL_HEIGHT,height,
            EGL_NONE,
        ]
        surface = eglCreatePbufferSurface(
            display, 
            configs[0],
            surface_attributes,
        )
    except GLError as err:
        log.error("Error code: %s on %s", err.err, err.baseOperation)
        raise
    eglBindAPI(API_MAP[api])
    ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
    if ctx == EGL_NO_CONTEXT:
        raise RuntimeError( 'Unable to create context' )
    eglMakeCurrent( display, surface, surface, ctx )
    yield ctx,surface 
    content = glReadPixelsub(0,0, width, height, GL_RGB, outputType=None)
    if output:
        write_ppm(content, output)
    # eglSwapBuffers( display, surface )

def main():
    with egl_context() as setup:
        ctx,surface = setup
        glClearColor(1.0,1.0,1.0,1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
