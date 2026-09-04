#! /usr/bin/env python3
"""Headless CGL backend for :class:`glcontext.ContextTestCase` (macOS).

CGL is the layer NSGL and AGL are built on, and the only one that hands out a
context with no window server to put a window on -- which is what a CI runner,
a batch tool or a remote shell has.  It is the macOS counterpart of
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
give.
"""

from __future__ import annotations

import logging
import os

from OpenGL import CGL

log = logging.getLogger(__name__)

_ES_APIS = ('gles', 'es')

#: The lowest GL version each CGL profile provides.  macOS answers a request
#: for 3.2 or above with a core profile and has no compatibility one there; the
#: legacy profile is 2.1 and is the only one with fixed function in it.
_PROFILE_FLOORS = (
    ((4, 1), 'core4'),
    ((3, 2), 'core3'),
    ((0, 0), 'legacy'),
)


def profile_for(api, profile, gl_version):
    """The CGL profile serving this request, or ``None`` with the reason why.

    Returns ``(profile_name, None)`` or ``(None, reason)``.  Pure, so what this
    backend will and will not serve is readable without a Mac: the two refusals
    are OpenGL-ES, which CGL does not provide at all, and a compatibility
    profile above 2.1, which macOS does not have.
    """
    if (api or 'gl').lower() in _ES_APIS:
        return None, 'CGL provides no OpenGL-ES contexts'
    major, minor = gl_version
    wants_core = (profile or 'compatibility').lower() == 'core'
    if not wants_core and (major, minor) > (2, 1):
        return None, (
            'macOS has no compatibility profile above 2.1; %d.%d was asked for'
            % (major, minor))
    if not wants_core:
        return 'legacy', None
    for floor, name in _PROFILE_FLOORS:
        if (major, minor) >= floor:
            if name == 'legacy':
                return None, (
                    'a core profile below 3.2 does not exist; %d.%d was asked '
                    'for' % (major, minor))
            return name, None
    return None, 'no CGL profile for %d.%d' % (major, minor)   # pragma: no cover


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
        except Exception as err:
            self._destroy_context()
            self.skipTest('no %dx%d offscreen target: %s'
                          % (self.width, self.height, err))

    def _swap(self):
        # Nothing is presented from a framebuffer object.  Tests read back with
        # glReadPixels, which finishes the pipeline on its own.
        pass

    def _destroy_context(self):
        if self._target is not None:
            self._target.release()
            self._target = None
        if self._cgl_manager is not None:
            manager, self._cgl_manager = self._cgl_manager, None
            self._cgl_context = None
            manager.__exit__(None, None, None)
