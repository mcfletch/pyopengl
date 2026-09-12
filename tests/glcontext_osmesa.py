#! /usr/bin/env python3
"""OSMesa backend for :class:`glcontext.ContextTestCase`.

Renders into an array the context owns, with no window system, no device node
and no drawable of any kind.  It is the fourth headless backend beside
``glcontext_egl`` (a GPU with no window), ``glcontext_cgl`` (macOS) and
``glcontext_wgl`` (Windows) -- and the one that needs least of the machine:
where those want a driver willing to hand out an off-screen surface, this
wants only ``libOSMesa``.

Selected with ``TEST_WINDOWING=osmesa``.  ``PYOPENGL_PLATFORM=osmesa`` has to
be set before anything imports OpenGL, and ``conftest`` does that from the same
``TEST_WINDOWING`` this reads, so a run asks for it in one place.

**The buffer is the default framebuffer**, so ``glClear``, ``glReadPixels`` and
the buffer queries a case makes against framebuffer zero all land where the
case expects.  CGL's headless context needs a framebuffer object bound in their
place; this does not, and neither does the WGL pbuffer.

**It is single-buffered**, which is the one place a case can tell this from a
window: there is no back buffer, so ``glDrawBuffer(GL_BACK)`` is
``GL_INVALID_OPERATION``.  ``OSMesaCreateContextAttribs`` offers no
double-buffer attribute -- OSMesa has exactly one buffer, the caller's -- so
this cannot be papered over as the WGL backend papers it over by asking for a
double-buffered pbuffer.  ``draw_buffer_name()`` says ``GL_FRONT`` here and the
state cases read it rather than assuming ``GL_BACK``.

**Software rasterisation, always.**  Nothing measured here says anything about
speed, so a run on this backend is a run for correctness: the ``performance``
marker is what a timing case carries and this backend is no reason to trust one.

``OpenGL.osmesa.offscreen`` holds the machinery; this is the part that answers
to the suite's fixture.
"""

from __future__ import annotations

import logging

from OpenGL.osmesa import offscreen

log = logging.getLogger(__name__)

#: OSMesa serves desktop OpenGL only.  An ES case asks for an API this has no
#: way to give, which is a skip rather than a lower context that would pass
#: while testing something else.
_ES_APIS = ('gles', 'es')


def profile_for(api, profile, gl_version):
    """The OSMesa profile serving this request, or ``None`` with the reason.

    Returns ``(profile_name, None)`` or ``(None, reason)``.  Pure, so what a
    request comes to can be read without a Mesa to ask.
    """
    if (api or 'gl').lower() in _ES_APIS:
        return (None, 'OSMesa provides no OpenGL-ES contexts')
    wanted = (profile or 'compatibility').lower()
    # `compat` is what the older cases in this suite spell it.
    if wanted in ('compat', 'compatibility'):
        return ('compatibility', None)
    if wanted == 'core':
        return ('core', None)
    return (None, 'no OSMesa profile for %r' % (profile,))


class OSMesaBackend(object):
    """Mixin supplying an OSMesa context rendering into its own buffer."""

    backend_name = 'osmesa'

    #: There is no window, so this backend is always headless and never dwells.
    visible = False

    _osmesa_context = None

    def _create_context(self):
        profile, refusal = profile_for(
            getattr(self, 'api', 'gl'),
            getattr(self, 'profile', 'compatibility'),
            self.gl_version,
        )
        if profile is None:
            self.skipTest(refusal)

        missing = offscreen.available()
        if missing:
            self.skipTest('no OSMesa here: %s missing' % (', '.join(missing),))
        try:
            self._osmesa_context = offscreen.OffscreenContext(
                width=self.width,
                height=self.height,
                profile=profile,
                version=tuple(self.gl_version),
                depth_bits=self.depth_size,
                stencil_bits=self.stencil_size,
                accum_bits=self.accum_size,
            )
        except offscreen.OSMesaError as err:
            self.skipTest('no OSMesa %s GL %d.%d context here: %s'
                          % ((profile,) + tuple(self.gl_version) + (err,)))
        log.info('OSMesa backend: %r', self._osmesa_context)

    def _make_current(self):
        if self._osmesa_context is None:
            raise RuntimeError('this backend has no context to make current')
        self._osmesa_context.make_current()

    def _swap(self):
        # Nothing is presented: the buffer the case reads is the one that was
        # drawn into.  glReadPixels finishes the pipeline on its own.
        pass

    def _destroy_context(self):
        if self._osmesa_context is not None:
            context, self._osmesa_context = self._osmesa_context, None
            context.release()
