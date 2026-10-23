#! /usr/bin/env python3
"""Headless CGL backend for :class:`glcontext.ContextTestCase` (macOS).

CGL creates a context with no window and no window server, so this backend
runs on a CI runner or over a remote shell.  It is the macOS counterpart of
``glcontext_egl``: no window, no display, and ``visible`` and the inter-test
dwell do not apply.

Selected with ``TEST_WINDOWING=cgl``.  ``TEST_CGL_RENDERER`` pins the renderer
kind (``accelerated`` / ``any`` / ``software``); unset, an accelerated renderer
is preferred and the CPU one taken where there is no other, so the same setting
works on a laptop and on a virtual machine.

**Framebuffer zero belongs to a drawable, and there is none**, so the backend
creates a framebuffer object of the requested size and binds it.  Every
``glClear``, ``glReadPixels`` and draw a test makes then lands where it expects,
and nothing in the test has to know.

What macOS does not have, this skips rather than pretends: there is no OpenGL-ES
through CGL, and no compatibility profile above 2.1 -- so a case wanting either
is skipped with the reason, which is what a platform that cannot serve it should
give.  A pixel format has no debug-context attribute either, so ``debug_context``
makes an ordinary context here; macOS caps at GL 4.1 and has no ``GL_KHR_debug``
to report through, and a case that needs the reporting checks for it.
"""

from __future__ import annotations

import logging
import os

from OpenGL import CGL
from OpenGL.CGL import profile_for
from OpenGL.error import GLError

log = logging.getLogger(__name__)

__all__ = ['CGLBackend', 'profile_for']

class CGLBackend(object):
    """Mixin supplying headless CGL context creation."""

    backend_name = 'cgl'

    #: there is no window, so this backend is always headless.
    visible = False

    _cgl_context = None
    _cgl_manager = None
    _target = None

    def _create_context(self):
        profile, refusal = profile_for(
            getattr(self, 'api', 'gl'),
            getattr(self, 'profile', 'compatibility'),
            self.gl_version,
        )
        if profile is None:
            self.skipTest(refusal)

        renderer = os.environ.get('TEST_CGL_RENDERER', '').strip().lower() or None
        manager = CGL.headless_context(
            profile=profile,
            renderer=renderer,
            color_size=self.red_size + self.green_size + self.blue_size,
            alpha_size=self.alpha_size,
            depth_size=self.depth_size,
            stencil_size=self.stencil_size,
        )
        try:
            context = manager.__enter__()
        except CGL.CGLError as err:
            self.skipTest('no CGL %s context here: %s' % (profile, err))
        self._cgl_manager = manager
        self._cgl_context = context
        try:
            self._target = CGL.OffscreenTarget(self.width, self.height)
        except (CGL.CGLError, GLError) as err:
            self._destroy_context()
            self.skipTest('no %dx%d offscreen target: %s'
                          % (self.width, self.height, err))

    def _swap(self):
        # Nothing is presented from a framebuffer object.  Tests read back with
        # glReadPixels, which finishes the pipeline on its own.
        pass

    def _make_current(self):
        if self._cgl_context is None:
            raise RuntimeError('this backend has no context to make current')
        CGL.library().CGLSetCurrentContext(self._cgl_context)

    def _destroy_context(self):
        if self._target is not None:
            self._target.release()
            self._target = None
        if self._cgl_manager is not None:
            manager, self._cgl_manager = self._cgl_manager, None
            self._cgl_context = None
            manager.__exit__(None, None, None)
