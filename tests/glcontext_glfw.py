#! /usr/bin/env python3
"""glfw windowing backend for :class:`glcontext.ContextTestCase`.

Implements the ``_create_context`` / ``_swap`` / ``_destroy_context`` hooks for
both desktop OpenGL and OpenGL-ES.  Which one is created is driven entirely by
the test's ``api`` attribute (``'gl'`` / ``'gles'``); ``profile`` /
``gl_version`` / the colour-depth-stencil-accum sizes / ``visible`` are honoured
the same way for both.  A context the driver will not provide skips the test
rather than failing it.
"""

from __future__ import print_function

import glfw

_PROFILES = {
    'core': glfw.OPENGL_CORE_PROFILE,
    'compatibility': glfw.OPENGL_COMPAT_PROFILE,
    'compat': glfw.OPENGL_COMPAT_PROFILE,
    'any': glfw.OPENGL_ANY_PROFILE,
}

_ES_APIS = ('gles', 'es')

_glfw_ready = False


def _ensure_glfw():
    global _glfw_ready
    if not _glfw_ready:
        if not glfw.init():
            raise RuntimeError('Failed to initialise glfw')
        _glfw_ready = True


class GLFWBackend(object):
    """Mixin supplying glfw-backed context creation (desktop GL or ES)."""

    #: identifies the backend to API bases that need to know (see glcontext_es).
    backend_name = 'glfw'

    _window = None

    def _create_context(self):
        _ensure_glfw()
        glfw.default_window_hints()

        api = getattr(self, 'api', 'gl').lower()
        major, minor = self.gl_version

        if api in _ES_APIS:
            glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_ES_API)
            # Force EGL so ES contexts work on desktop drivers.
            glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.EGL_CONTEXT_API)
        else:
            glfw.window_hint(glfw.CLIENT_API, glfw.OPENGL_API)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, major)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, minor)

        # GL profiles only exist for desktop GL >= 3.2.
        profile = getattr(self, 'profile', 'compatibility').lower()
        if api not in _ES_APIS and (major, minor) >= (3, 2):
            glfw.window_hint(glfw.OPENGL_PROFILE, _PROFILES[profile])
            if profile == 'core':
                glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

        glfw.window_hint(glfw.RED_BITS, self.red_size)
        glfw.window_hint(glfw.GREEN_BITS, self.green_size)
        glfw.window_hint(glfw.BLUE_BITS, self.blue_size)
        glfw.window_hint(glfw.ALPHA_BITS, self.alpha_size)
        glfw.window_hint(glfw.DEPTH_BITS, self.depth_size)
        glfw.window_hint(glfw.STENCIL_BITS, self.stencil_size)

        accum = getattr(self, 'accum_size', 0)
        for hint in (
            'ACCUM_RED_BITS',
            'ACCUM_GREEN_BITS',
            'ACCUM_BLUE_BITS',
            'ACCUM_ALPHA_BITS',
        ):
            glfw.window_hint(getattr(glfw, hint), accum)

        glfw.window_hint(glfw.VISIBLE, glfw.TRUE if self.visible else glfw.FALSE)

        try:
            window = glfw.create_window(
                self.width, self.height, self._window_title(), None, None
            )
        except glfw.GLFWError as err:
            window = None
            reason = str(err)
        else:
            reason = 'driver did not provide the requested context'

        if not window:
            self.skipTest(
                'Could not create a %s %s %d.%d context via glfw: %s'
                % (api, profile, major, minor, reason)
            )

        self._window = window
        glfw.make_context_current(window)

    def _window_title(self):
        return '%s (%s %d.%d %s)' % (
            type(self).__name__,
            getattr(self, 'api', 'gl'),
            self.gl_version[0],
            self.gl_version[1],
            getattr(self, 'profile', ''),
        )

    def _swap(self):
        if self._window is not None:
            glfw.swap_buffers(self._window)

    def _forget_context(self, handle):
        """Tell the dispatch layer a context is gone.

        Its table is keyed by the GL context handle, and a handle is an
        address the driver is free to hand out again.  Leaving the table
        behind means the next context that lands on that address inherits a
        dead context's resolved function pointers -- not a leak but a wrong
        answer, and one that shows up as a test passing for the wrong reason
        or a call into a function the new context does not have.
        """
        if not handle:
            return
        try:
            from OpenGL import _dispatch
        except ImportError:  # pragma: no cover - ctypes-only build
            return
        _dispatch.forget_context(int(handle))

    def _destroy_context(self):
        if self._window is not None:
            # Read the GL context's own handle while the window is still
            # current: that, not the window pointer, is what the table is
            # keyed by.
            handle = None
            try:
                from OpenGL import platform

                glfw.make_context_current(self._window)
                handle = platform.PLATFORM.GetCurrentContext()
            except Exception:  # pragma: no cover - a context already gone
                handle = None
            glfw.destroy_window(self._window)
            self._window = None
            self._forget_context(handle)
