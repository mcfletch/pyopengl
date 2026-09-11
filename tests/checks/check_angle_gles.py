#! /usr/bin/env python
# requires: angle
"""Render through ANGLE and read the result back, all of it through PyOpenGL.

A whole GLES context from PyOpenGL's own bindings on the ANGLE platform: EGL
picks a config and makes a pbuffer current, GLES2 clears it to a colour chosen
so no channel equals another, and ``glReadPixels`` says what actually landed in
the framebuffer. A binding that resolved to the wrong library, or a platform
that had quietly given out desktop GL, does not survive the read back.

A script rather than a test case because a platform is chosen once per process,
at import: this has to *be* the process.
"""
import os

os.environ.setdefault('PYOPENGL_PLATFORM', 'angle')

import checkutils  # noqa: E402  -- after the platform is pinned

from OpenGL import platform  # noqa: E402
from OpenGL.EGL import (  # noqa: E402
    EGL_ALPHA_SIZE, EGL_BLUE_SIZE, EGL_CONTEXT_CLIENT_VERSION, EGL_DEFAULT_DISPLAY,
    EGL_DEPTH_SIZE, EGL_GREEN_SIZE, EGL_HEIGHT, EGL_NONE, EGL_NO_CONTEXT,
    EGL_OPENGL_ES2_BIT, EGL_OPENGL_ES_API, EGL_PBUFFER_BIT, EGL_RED_SIZE,
    EGL_RENDERABLE_TYPE, EGL_SURFACE_TYPE, EGL_WIDTH, EGLConfig, EGLint,
    eglBindAPI, eglChooseConfig, eglCreateContext, eglCreatePbufferSurface,
    eglGetDisplay, eglInitialize, eglMakeCurrent,
)
from OpenGL.GLES2 import (  # noqa: E402
    GL_COLOR_BUFFER_BIT, GL_RGBA, GL_UNSIGNED_BYTE, GL_VERSION,
    glClear, glClearColor, glFinish, glGetString, glReadPixels, glViewport,
)

SIZE = 64
#: No two channels alike, so a swapped or truncated component shows up.
COLOUR = (0.25, 0.5, 0.75, 1.0)
EXPECTED = (64, 128, 191, 255)


def main():
    if platform.PLATFORM.GL is not None:
        raise SystemExit('the ANGLE platform offered a desktop GL library')

    display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
    major, minor = EGLint(), EGLint()
    if not eglInitialize(display, major, minor):
        checkutils.skip('ANGLE is present but eglInitialize failed')
    if not eglBindAPI(EGL_OPENGL_ES_API):
        raise SystemExit('eglBindAPI(EGL_OPENGL_ES_API) failed')

    wanted = [
        EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8, EGL_DEPTH_SIZE, 16,
        EGL_NONE,
    ]
    configs, count = (EGLConfig * 1)(), EGLint()
    if not eglChooseConfig(display, (EGLint * len(wanted))(*wanted),
                           configs, 1, count) or not count.value:
        checkutils.skip('ANGLE offered no RGBA8 pbuffer config')

    surface = eglCreatePbufferSurface(
        display, configs[0],
        (EGLint * 5)(EGL_WIDTH, SIZE, EGL_HEIGHT, SIZE, EGL_NONE))
    context = eglCreateContext(
        display, configs[0], EGL_NO_CONTEXT,
        (EGLint * 3)(EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE))
    if not surface or not context:
        raise SystemExit('ANGLE would not give a pbuffer and a context')
    if not eglMakeCurrent(display, surface, surface, context):
        raise SystemExit('eglMakeCurrent failed')

    version = glGetString(GL_VERSION).decode()
    if 'ES' not in version:
        raise SystemExit('expected an OpenGL ES version, got %r' % (version,))

    glViewport(0, 0, SIZE, SIZE)
    glClearColor(*COLOUR)
    glClear(GL_COLOR_BUFFER_BIT)
    glFinish()
    data = bytes(glReadPixels(0, 0, SIZE, SIZE, GL_RGBA, GL_UNSIGNED_BYTE))
    if len(data) != SIZE * SIZE * 4:
        raise SystemExit('read back %d bytes, wanted %d'
                         % (len(data), SIZE * SIZE * 4))
    got = tuple(data[:4])
    # One count of rounding either way: the framebuffer is 8 bits a channel and
    # the clear colour is a float.
    if any(abs(a - b) > 1 for a, b in zip(got, EXPECTED)):
        raise SystemExit('first pixel was %r, wanted %r' % (got, EXPECTED))

    print('OK')


if __name__ == '__main__':
    main()
