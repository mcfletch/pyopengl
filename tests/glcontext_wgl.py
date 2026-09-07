#! /usr/bin/env python3
"""Headless WGL backend for :class:`glcontext.ContextTestCase` (Windows).

Renders on a pbuffer -- a drawable the display driver allocates out of its own
memory, belonging to no window and appearing nowhere.  It is the Windows
counterpart of ``glcontext_egl`` and ``glcontext_cgl``: no window, no message
loop, nothing on screen, and ``visible`` and the inter-test dwell do not apply.

Selected with ``TEST_WINDOWING=wgl``.  Nothing else has to be set: WGL is the
platform's own binding for OpenGL, so unlike the EGL backend there is no
``PYOPENGL_PLATFORM`` to pin.

**A pbuffer is the default framebuffer**, so ``glClear``, ``glReadPixels`` and
the buffer queries a case makes against framebuffer zero all land where the
case expects -- CGL's headless context needs a framebuffer object bound in
their place, and this does not.

**It is double-buffered**, which an offscreen surface has no other reason to
be: nothing presents it and ``_swap`` does nothing.  The suite is written
against a window, and a window has a back buffer -- ``glDrawBuffer(GL_BACK)``
and ``glDrawBuffers([GL_BACK])`` are GL_INVALID_OPERATION where there is none,
and the GL 1.x and 2.0 state cases make both.  Asking for one is what makes
this backend the same shape as the windowed ones rather than a second kind of
target every case has to know about.  A renderer wants the single-buffered
default that ``OpenGL.WGL.offscreen`` gives; a stand-in for a window does not.

What Windows does not have, this skips rather than pretends: WGL provides no
OpenGL-ES contexts, and a driver with no ``WGL_ARB_pbuffer`` provides no
offscreen surface at all.  Both are skipped with the reason, which is what a
platform that cannot serve a case should give.

``OpenGL.WGL.offscreen`` holds the machinery; this is the part that answers to
the suite's fixture.
"""

from __future__ import annotations

import logging

from OpenGL.WGL import offscreen

log = logging.getLogger(__name__)

_ES_APIS = ('gles', 'es')


def profile_for(api, profile, gl_version):
    """The WGL profile serving this request, or ``None`` with the reason why.

    Returns ``(profile_name, None)`` or ``(None, reason)``.  Pure, so what this
    backend will and will not serve is readable without Windows.

    The profile mask arrived with GL 3.2, and ``wglCreateContextAttribsARB``
    refuses a request below that which carries one -- so a case asking for 2.1
    gets ``'legacy'``, which names no profile and is the fixed-function
    pipeline every driver still provides.
    """
    if (api or 'gl').lower() in _ES_APIS:
        return None, 'WGL provides no OpenGL-ES contexts'
    if tuple(gl_version) < (3, 2):
        return 'legacy', None
    return ('core' if (profile or 'compatibility').lower() == 'core'
            else 'compatibility'), None


class WGLBackend(object):
    """Mixin supplying headless WGL pbuffer context creation."""

    backend_name = 'wgl'

    #: there is no window, so this backend is always headless.
    visible = False

    _wgl_context = None

    def _create_context(self):
        profile, refusal = profile_for(
            getattr(self, 'api', 'gl'),
            getattr(self, 'profile', 'compatibility'),
            self.gl_version,
        )
        if profile is None:
            self.skipTest(refusal)

        missing = offscreen.available(profile)
        if missing:
            self.skipTest('this driver offers no offscreen OpenGL: %s missing'
                          % (', '.join(missing),))
        try:
            self._wgl_context = offscreen.OffscreenContext(
                width=self.width,
                height=self.height,
                profile=profile,
                version=tuple(self.gl_version),
                color_bits=self.red_size + self.green_size + self.blue_size,
                alpha_bits=self.alpha_size,
                depth_bits=self.depth_size,
                stencil_bits=self.stencil_size,
                double_buffer=True,
            )
        except offscreen.WGLError as err:
            self.skipTest('no WGL %s GL %d.%d context here: %s'
                          % ((profile,) + tuple(self.gl_version) + (err,)))
        log.info('WGL offscreen backend: %r', self._wgl_context)

    def _make_current(self):
        if self._wgl_context is None:
            raise RuntimeError('this backend has no context to make current')
        self._wgl_context.make_current()

    def _swap(self):
        # Nothing is presented from a pbuffer.  Tests read back with
        # glReadPixels, which finishes the pipeline on its own.
        pass

    def _destroy_context(self):
        # Without the notification: whether the dispatch layer is told is the
        # fixture's to decide, and ``_release_context`` is where it decides it.
        # A case about what a program that never notifies PyOpenGL faces asks
        # for this one directly, and the context object doing it anyway would
        # leave that case unable to reach the state it is about.
        if self._wgl_context is not None:
            context, self._wgl_context = self._wgl_context, None
            context.release(forget=False)
