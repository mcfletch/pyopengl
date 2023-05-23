#! /usr/bin/env python3
"""Raw xlib based test setup"""
from Xlib import X, display, error
import ctypes
from functools import wraps

from OpenGL import arrays
from OpenGL.EGL import *

DESIRED_ATTRIBUTES = [
    EGL_BLUE_SIZE,
    8,
    EGL_RED_SIZE,
    8,
    EGL_GREEN_SIZE,
    8,
    EGL_DEPTH_SIZE,
    24,
    EGL_COLOR_BUFFER_TYPE,
    EGL_RGB_BUFFER,
    EGL_CONFIG_CAVEAT,
    EGL_NONE,  # Don't allow slow/non-conformant
]
API_BITS = {
    "opengl": EGL_OPENGL_BIT,
    "gl": EGL_OPENGL_BIT,
    "gles2": EGL_OPENGL_ES2_BIT,
    "gles1": EGL_OPENGL_ES_BIT,
    "gles": EGL_OPENGL_ES_BIT,
    "es2": EGL_OPENGL_ES2_BIT,
    "es1": EGL_OPENGL_ES_BIT,
    "es": EGL_OPENGL_ES_BIT,
}
API_NAMES = dict(
    [
        (
            k,
            {
                EGL_OPENGL_BIT: EGL_OPENGL_API,
                EGL_OPENGL_ES2_BIT: EGL_OPENGL_ES_API,
                EGL_OPENGL_ES_BIT: EGL_OPENGL_ES_API,
            }[v],
        )
        for k, v in API_BITS.items()
    ]
)


class EGLWindow(object):
    def __init__(
        self, display, msg, size=(300, 300), api='es2', attributes=DESIRED_ATTRIBUTES
    ):
        self.display = display
        self.msg = msg

        self.screen: Xlib.Window = self.display.screen()
        self.window = self.screen.root.create_window(
            50,
            50,
            size[0],
            size[1],
            2,
            self.screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,
            # special attribute values
            background_pixel=self.screen.white_pixel,
            event_mask=(
                X.ExposureMask
                | X.ResizeRedirectMask
                | X.StructureNotifyMask
                | X.ButtonPressMask
                | X.ButtonReleaseMask
                | X.Button1MotionMask
            ),
            colormap=X.CopyFromParent,
        )
        self.gc = self.window.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )
        self.window.map()
        self.api = api
        self.attributes = attributes

    egl_ctx = None

    def eglSetup(self):
        """Setup the EGL rendering context"""
        if self.egl_ctx is not None:
            return
        major, minor = ctypes.c_long(), ctypes.c_long()
        self.egl_display = display = eglGetDisplay(EGL_DEFAULT_DISPLAY)
        eglInitialize(display, major, minor)
        num_configs = ctypes.c_long()
        configs = (EGLConfig * 2)()
        api_constant = API_NAMES[self.api.lower()]
        print('api requested:', self.api, ' api constant', api_constant)
        local_attributes = self.attributes[:]
        local_attributes.extend(
            [
                EGL_CONFORMANT,
                API_BITS[self.api.lower()],
                EGL_NONE,
            ]
        )
        print("local_attributes", local_attributes)
        local_attributes = arrays.GLintArray.asArray(local_attributes)
        eglChooseConfig(display, local_attributes, configs, 2, num_configs)
        if num_configs.value < 1:
            raise RuntimeError("Unable to find a suitable config")
        print("API", api_constant)
        eglBindAPI(api_constant)
        window = self.window.id
        self.egl_surface = eglCreateWindowSurface(display, configs[0], window, None)

        self.egl_ctx = eglCreateContext(display, configs[0], EGL_NO_CONTEXT, None)
        if self.egl_ctx == EGL_NO_CONTEXT:
            raise RuntimeError("Unable to create context")

    def loop(self, target, args, named, exit_on_render=False):
        do_close = True
        try:
            while True:
                try:
                    e = self.display.next_event()
                except error.ConnectionClosedError as err:
                    do_close = False
                    return

                if e.type == X.Expose:
                    self.eglSetup()
                    eglMakeCurrent(
                        self.egl_display,
                        self.egl_surface,
                        self.egl_surface,
                        self.egl_ctx,
                    )
                    target(*args, **named)
                    eglSwapBuffers(self.egl_display, self.egl_surface)
                    if exit_on_render:
                        return

                elif e.type == X.KeyPress:
                    return
        finally:
            if do_close:
                self.close()

    def close(self):
        self.window.destroy()


def egltest(size=(300, 300), name=None, api="es2", attributes=DESIRED_ATTRIBUTES):
    def gltest(function):
        """Decorator to allow a function to run in a Pygame GLES[1,2,3] context"""

        @wraps(function)
        def test_function(*args, **named):
            window = EGLWindow(
                display.Display(),
                name or function.__name__,
                api=api,
                attributes=attributes,
            )
            window.loop(target=function, args=args, named=named, exit_on_render=True)

        return test_function

    return gltest


if __name__ == "__main__":

    @egltest()
    def test_sample(*args, **named):
        print("Ran sample")

    test_sample()
    test_sample()
    test_sample()
