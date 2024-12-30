#! /usr/bin/env python
"""Implements the functionality in MESA's EGL + OpenGL demo1:

    http://cgit.freedesktop.org/mesa/demos/tree/src/egl/opengl/demo1.c

Basically just to check if the EGL code works...

NOTE: this test program is both MIT (MESA) and GPLv2 licensed due to use of 
sample code from python-Xlib.
"""
import pygame.display
import pygame
import os
import logging
import numpy

if not os.environ.get("PYOPENGL_PLATFORM"):
    os.environ["PYOPENGL_PLATFORM"] = "egl"

import OpenGL, ctypes

OpenGL.setPlatform("egl")

if os.environ.get("TEST_NO_ACCELERATE"):
    OpenGL.USE_ACCELERATE = False
from OpenGL._bytes import as_str
from OpenGL.EGL import *
from OpenGL.error import GLError

log = logging.getLogger(__name__)
import sys
from OpenGL.arrays.vbo import VBO


def describe_config(display, config):
    """Describe the given configuration"""
    parameters = (
        EGL_CONFIG_ID,
        EGL_CONFIG_CAVEAT,
        EGL_CONFORMANT,
        EGL_LEVEL,
        EGL_NATIVE_RENDERABLE,
        EGL_NATIVE_VISUAL_ID,
        EGL_NATIVE_VISUAL_TYPE,
        EGL_SURFACE_TYPE,
        EGL_ALPHA_SIZE,
        EGL_ALPHA_MASK_SIZE,
        EGL_BIND_TO_TEXTURE_RGB,
        EGL_BIND_TO_TEXTURE_RGBA,
        EGL_BLUE_SIZE,
        EGL_BUFFER_SIZE,
        EGL_COLOR_BUFFER_TYPE,
        EGL_DEPTH_SIZE,
        EGL_GREEN_SIZE,
        EGL_LUMINANCE_SIZE,
        EGL_MAX_PBUFFER_WIDTH,
        EGL_MAX_PBUFFER_HEIGHT,
        EGL_MAX_PBUFFER_PIXELS,
        EGL_MAX_SWAP_INTERVAL,
        EGL_MIN_SWAP_INTERVAL,
        EGL_RED_SIZE,
        EGL_RENDERABLE_TYPE,
        EGL_SAMPLE_BUFFERS,
        EGL_SAMPLES,
        EGL_STENCIL_SIZE,
        EGL_TRANSPARENT_TYPE,
        EGL_TRANSPARENT_RED_VALUE,
        EGL_TRANSPARENT_GREEN_VALUE,
        EGL_TRANSPARENT_BLUE_VALUE,
    )
    description = []
    for param in parameters:
        value = ctypes.c_long()
        eglGetConfigAttrib(display, config, param, value)
        description.append(
            "%s = %s"
            % (
                param,
                value.value,
            )
        )
    return "\n".join(description)


def mainloop(displayfunc):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        if not displayfunc():
            return False
        return True


def main(displayfunc, api):
    major, minor = ctypes.c_long(), ctypes.c_long()
    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    log.info("Display return value: %s", display)
    log.info("Display address: %s", display.address)
    # display = display.as_voidp
    # print 'wrapped', display
    if not eglInitialize(display, major, minor):
        log.error("Unable to initialize")
        return
    log.info("EGL version %s.%s", major.value, minor.value)

    num_configs = ctypes.c_long()
    eglGetConfigs(display, None, 0, num_configs)
    log.info("%s configs", num_configs.value)

    configs = (EGLConfig * num_configs.value)()
    eglGetConfigs(display, configs, num_configs.value, num_configs)

    bit = EGL_OPENGL_API
    if api == 'gles':
        bit = EGL_OPENGL_ES_BIT
    elif api == 'gles2':
        bit = EGL_OPENGL_ES2_BIT
    attributes = [
        EGL_NATIVE_RENDERABLE,
        EGL_TRUE,
        EGL_CONFORMANT,
        bit,
        EGL_COLOR_BUFFER_TYPE,
        EGL_RGB_BUFFER,
        EGL_NONE,
    ]
    attributes = (EGLint * len(attributes))(*attributes)
    eglChooseConfig(display, attributes, configs, len(configs), num_configs)

    for number, config_id in enumerate(configs):
        # print config_id
        log.info("Config #%d\n%s", number, describe_config(display, config_id))
        break

    log.info("Attempting to bind and create contexts/apis for %s", api)
    try:
        eglBindAPI(0x3333)  # junk value
    except GLError:
        pass
    else:
        assert False, "Should have generated error on bind to non-existent api"
    eglBindAPI(api)

    # now need to get a raw X window handle...
    pygame.init()

    pygame.display.set_mode((500, 500), flags=pygame.NOFRAME | pygame.SHOWN)
    # pygame.display.init()
    window = pygame.display.get_wm_info()["window"]

    # print("Clearing current context")
    # eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT)

    surface = eglCreateWindowSurface(display, configs[0], window, None)
    if surface == EGL_NO_SURFACE:
        raise RuntimeError("No surface could be created")

    ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
    if ctx == EGL_NO_CONTEXT:
        log.error("Unable to create the regular context")
        return
    else:
        log.info("Created regular context")

        def _displayfunc():
            try:
                displayfunc(display, surface, ctx)
            except Exception:
                log.exception("Failure during display function")
                return False
            else:
                return True

        if not mainloop(_displayfunc):
            raise RuntimeError("Display func crashed")

    pbufAttribs = (EGLint * 5)(*[EGL_WIDTH, 500, EGL_HEIGHT, 500, EGL_NONE])
    pbuffer = eglCreatePbufferSurface(display, configs[0], pbufAttribs)
    if pbuffer == EGL_NO_SURFACE:
        log.error("Unable to create pbuffer surface")
    else:
        log.info("created pbuffer surface")
    log.info(
        "Available EGL extensions:\n  %s",
        "\n  ".join([as_str(ext) for ext in EGLQuerier.getExtensions().split()]),
    )
    print('OK')


def displayfunc_gl(display, surface, ctx):
    from OpenGL import GL

    eglMakeCurrent(display, surface, surface, ctx)
    GL.glClearColor(1, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    eglSwapBuffers(display, surface)


displayfunc_gl.api = EGL_OPENGL_API


def displayfunc_gles1(display, surface, ctx):
    from OpenGL import GLES1 as GL

    eglMakeCurrent(display, surface, surface, ctx)
    GL.glClearColor(1, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    vertices = numpy.array(((1, 0, 0), (-1, 0, 0), (0, 1, 0)), "f")
    GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
    GL.glVertexPointer(3, GL.GL_FLOAT, 0, vertices)
    GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
    eglSwapBuffers(display, surface)


displayfunc_gles1.api = EGL_OPENGL_ES_API


shader = None


def displayfunc_gles2(display, surface, ctx):
    from OpenGL import GLES2 as GL
    from OpenGL.GLES2 import shaders

    eglMakeCurrent(display, surface, surface, ctx)
    GL.glClearColor(1, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    global shader, vbo, position_location, stride
    if shader is None:
        shader = shaders.compileProgram(
            shaders.compileShader(
                """#version 130
    attribute vec3 position;
    void main() {
        gl_Position = vec4( position, 0 );
    }""",
                type=GL_VERTEX_SHADER,
            ),
            shaders.compileShader(
                """#version 130
    void main() {
        gl_FragColor = vec4( 1,0,0,0 );
    }""",
                type=GL_FRAGMENT_SHADER,
            ),
        )
        vbo = VBO(
            array(
                [
                    (0, 1, 0),
                    (1, -1, 0),
                    (-1, -1, 0),
                ],
                dtype="f",
            )
        )
        position_location = GL.glGetAttribLocation(self.shader, "position")
        stride = 3 * 4
    with vbo:
        with shader:
            GL.glEnableVertexAttribArray(position_location)
            stride = 3 * 4
            GL.glVertexAttribPointer(
                position_location, 3, GL_FLOAT, False, stride, self.vbo
            )
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
    eglSwapBuffers(display, surface)


displayfunc_gles2.api = EGL_OPENGL_ES_API


def displayfunc_gles3(display, surface, ctx):
    from OpenGL import GLES3 as GL

    eglMakeCurrent(display, surface, surface, ctx)
    GL.glClearColor(1, 0, 0, 0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    eglSwapBuffers(display, surface)


displayfunc_gles3.api = EGL_OPENGL_ES_API


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if sys.argv[1:]:
        name = sys.argv[1]
    else:
        name = "gl"
    if name == "gles":
        name = "gles1"
    function = globals().get("displayfunc_%s" % (name,), displayfunc_gl)
    log.info("Using function: %s", function)
    main(function, function.api)
