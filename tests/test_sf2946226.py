import unittest
import OpenGL
from basetestcase import BaseTest
from OpenGL.GL import *
from OpenGL.GL.EXT.framebuffer_object import *


class TestSF2946226(BaseTest):
    """Regression for SF#2946226.

    Attaching a texture to an EXT framebuffer object used to raise spuriously
    when the C accelerator was disabled. ``OpenGL.USE_ACCELERATE`` is an
    import-time flag and cannot be flipped here, so this test only runs when the
    accelerator is already off -- run the suite with ``TEST_NO_ACCELERATE=1`` to
    exercise it; otherwise it is skipped.
    """

    @unittest.skipIf(
        OpenGL.USE_ACCELERATE,
        "requires the C accelerator disabled (run with TEST_NO_ACCELERATE=1)",
    )
    def test_framebuffer_texture_2d_ext(self):
        if not glGenFramebuffersEXT:
            self.skipTest('EXT_framebuffer_object not supported')

        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glBindTexture(GL_TEXTURE_2D, 0)

        fbo = glGenFramebuffersEXT(1)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)
        glBindTexture(GL_TEXTURE_2D, tex)

        # This call used to raise spuriously (SF#2946226); it should succeed.
        glFramebufferTexture2DEXT(
            GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_2D, tex, 0
        )
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)

