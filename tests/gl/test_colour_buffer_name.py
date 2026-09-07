#! /usr/bin/env python3
"""Which colour buffer a case may select depends on what is bound to draw into.

``GL_BACK`` and the per-eye names belong to the default framebuffer.  A
framebuffer object accepts only ``GL_NONE`` and ``GL_COLOR_ATTACHMENT``*i*, and
answers ``GL_INVALID_OPERATION`` for anything else -- so ``glDrawBuffer(GL_BACK)``
is right on one and a failure on the other.

Which is bound is the backend's choice, not the case's: the CGL backend draws
into a framebuffer object because framebuffer zero belongs to a drawable and
macOS's headless contexts have none, while the others draw into framebuffer
zero.  So a case that selects a buffer asks
:meth:`colour_buffer_name` rather than naming one.
"""

import unittest

from arraycompat import object_names, one
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestTheColourBufferName(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_it_names_something_the_bound_framebuffer_accepts(self):
        """Whichever framebuffer this backend gave, the answer is usable."""
        glDrawBuffer(self.colour_buffer_name())
        glReadBuffer(self.colour_buffer_name())
        self.check_error('selecting the buffer this framebuffer has')

    def test_a_framebuffer_object_is_named_by_its_attachment(self):
        self.require_extension('GL_ARB_framebuffer_object')
        fbo = one(glGenFramebuffers(1))
        self.defer_cleanup(lambda: glDeleteFramebuffers(1, object_names(fbo)))
        with self.framebuffer(fbo):
            assert self.colour_buffer_name() == GL_COLOR_ATTACHMENT0

    def test_and_the_default_framebuffer_by_its_back_buffer(self):
        """Only where this backend has one to bind -- CGL does not."""
        if self.draw_framebuffer():
            self.skipTest('this backend draws into a framebuffer object')
        assert self.colour_buffer_name() == GL_BACK_LEFT


if __name__ == '__main__':
    unittest.main()
