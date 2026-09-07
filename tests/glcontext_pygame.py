#! /usr/bin/env python3
"""pygame (SDL) windowing backend for :class:`glcontext.ContextTestCase`.

Implements the ``_create_context`` / ``_swap`` / ``_destroy_context`` hooks
using ``pygame.display``.  The requested ``gl_version`` / ``profile`` /
colour-depth-stencil-accum sizes are pushed through SDL's GL attributes before
``set_mode`` creates the context; a request the driver will not honour skips the
test rather than failing it.

ES note: SDL can be asked for an ES profile, but whether a usable ES context
results is driver-dependent.  The ES API base (glcontext_es) decides whether to
run ES tests on this backend at all; this module just creates whatever SDL
gives us.
"""

from __future__ import print_function

import pygame
import pygame.display

_ES_APIS = ('gles', 'es')


def _set_attr(name, value):
    """Best-effort ``gl_set_attribute`` for an attribute that may be absent."""
    const = getattr(pygame, name, None)
    if const is not None:
        pygame.display.gl_set_attribute(const, value)


class PygameBackend(object):
    """Mixin supplying pygame/SDL-backed context creation."""

    backend_name = 'pygame'

    _screen = None

    def _create_context(self):
        pygame.display.init()

        major, minor = self.gl_version
        api = getattr(self, 'api', 'gl').lower()
        profile = getattr(self, 'profile', 'compatibility').lower()

        _set_attr('GL_CONTEXT_MAJOR_VERSION', major)
        _set_attr('GL_CONTEXT_MINOR_VERSION', minor)

        mask = None
        if api in _ES_APIS:
            mask = getattr(pygame, 'GL_CONTEXT_PROFILE_ES', None)
        elif (major, minor) >= (3, 2):
            mask = getattr(
                pygame,
                'GL_CONTEXT_PROFILE_CORE'
                if profile == 'core'
                else 'GL_CONTEXT_PROFILE_COMPATIBILITY',
                None,
            )
        if mask is not None:
            try:
                pygame.display.gl_set_attribute(
                    pygame.GL_CONTEXT_PROFILE_MASK, mask
                )
            except pygame.error:
                pass

        _set_attr('GL_RED_SIZE', self.red_size)
        _set_attr('GL_GREEN_SIZE', self.green_size)
        _set_attr('GL_BLUE_SIZE', self.blue_size)
        _set_attr('GL_ALPHA_SIZE', self.alpha_size)
        _set_attr('GL_DEPTH_SIZE', self.depth_size)
        _set_attr('GL_STENCIL_SIZE', self.stencil_size)

        accum = getattr(self, 'accum_size', 0)
        if accum:
            for name in (
                'GL_ACCUM_RED_SIZE',
                'GL_ACCUM_GREEN_SIZE',
                'GL_ACCUM_BLUE_SIZE',
                'GL_ACCUM_ALPHA_SIZE',
            ):
                _set_attr(name, accum)

        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if not self.visible:
            # pygame.HIDDEN was added in pygame 2.0; fall back gracefully.
            flags |= getattr(pygame, 'HIDDEN', 0)

        try:
            self._screen = pygame.display.set_mode((self.width, self.height), flags)
        except pygame.error as err:
            pygame.display.quit()
            self.skipTest(
                'Could not create a %s %s %d.%d context via pygame: %s'
                % (api, profile, major, minor, err)
            )

        pygame.display.set_caption(self._window_title())

    def _window_title(self):
        return '%s (%s %d.%d %s)' % (
            type(self).__name__,
            getattr(self, 'api', 'gl'),
            self.gl_version[0],
            self.gl_version[1],
            getattr(self, 'profile', ''),
        )

    def _swap(self):
        if self._screen is not None:
            pygame.display.flip()

    def _make_current(self):
        """SDL keeps its one display context current, so there is nothing to
        switch to: a second context is a second display, which pygame does not
        offer.  A case wanting two at once asks for a backend that has them."""
        if self._screen is None:
            raise RuntimeError('this backend has no context to make current')

    def _destroy_context(self):
        if self._screen is not None:
            pygame.display.quit()
            self._screen = None
