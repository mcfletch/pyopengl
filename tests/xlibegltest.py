#! /usr/bin/env python3
"""Raw xlib based test setup"""
import checkutils

# python-xlib reaches for fcntl, so it is importable only on a Unix host; the
# checks built on this run nowhere else.
checkutils.require('Xlib.display')
from Xlib import X, display, error
import ctypes
import os
from functools import wraps

#: show the window by default (set TEST_VISIBLE=0 for headless/CI runs).
TEST_VISIBLE = os.environ.get('TEST_VISIBLE', '1').lower() not in ('0', 'false', 'no')

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
#: The client version an ES context has to ask for by name.  EGL defaults to
#: version 1, so an ``es2`` request left unsaid comes back as an ES1 context and
#: the first ES2 shader handed to it is what finds out.  Desktop GL takes its
#: version from the config and wants no attribute here.
API_CLIENT_VERSIONS = {
    EGL_OPENGL_ES2_BIT: 2,
    EGL_OPENGL_ES_BIT: 1,
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
        event_mask = (
            X.ExposureMask
            | X.ResizeRedirectMask
            | X.StructureNotifyMask
            | X.ButtonPressMask
            | X.ButtonReleaseMask
            | X.Button1MotionMask
        )
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
            event_mask=event_mask,
            colormap=X.CopyFromParent,
        )
        self.gc = self.window.create_gc(
            foreground=self.screen.black_pixel,
            background=self.screen.white_pixel,
        )
        # mapping the window is what makes it appear on screen; skip it for
        # headless/CI runs (the EGL window surface still works unmapped).
        if TEST_VISIBLE:
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
                # EGL_RENDERABLE_TYPE is what says which client API a config
                # can make a context for; EGL_CONFORMANT only says which it is
                # conformant to.  Asked for conformance alone, the match falls
                # back on the default renderable type -- desktop GL -- and the
                # ES context that config yields cannot be made current.
                EGL_RENDERABLE_TYPE,
                API_BITS[self.api.lower()],
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

        client_version = API_CLIENT_VERSIONS.get(API_BITS[self.api.lower()])
        context_attributes = None
        if client_version is not None:
            context_attributes = arrays.GLintArray.asArray([
                EGL_CONTEXT_CLIENT_VERSION,
                client_version,
                EGL_NONE,
            ])
        self.egl_ctx = eglCreateContext(
            display, configs[0], EGL_NO_CONTEXT, context_attributes
        )
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
                    if not eglMakeCurrent(
                        self.egl_display,
                        self.egl_surface,
                        self.egl_surface,
                        self.egl_ctx,
                    ):
                        # Unchecked, the target draws into no context at all:
                        # every glGet answers None and the first shader fails
                        # to compile with an empty log, which says nothing
                        # about the context never having been made current.
                        err = eglGetError()
                        if err == EGL_BAD_MATCH:
                            # The config was chosen renderable for this API and
                            # the driver made the context, so a refusal to pair
                            # them is the driver declining to provide the API
                            # rather than a mismatch this asked for.
                            checkutils.skip(
                                '%s contexts cannot be made current on this '
                                'driver (EGL_BAD_MATCH)' % (self.api,)
                            )
                        raise RuntimeError(
                            'eglMakeCurrent failed (EGL error 0x%x)' % (err,)
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
            # python-xlib defers the parts of itself that are Unix-only until a
            # display is opened, so this is where a host with no X server says
            # so -- as ImportError for the missing modules, DisplayError for a
            # server it cannot reach.
            try:
                server = display.Display()
            except (ImportError, error.DisplayError, OSError) as err:
                checkutils.skip('no X display available: %s' % (err,))
            window = EGLWindow(
                server,
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
