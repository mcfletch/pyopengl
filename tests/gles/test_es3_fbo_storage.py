#! /usr/bin/env python3
"""GLES3.0: immutable storage, multisample renderbuffers, clear-buffer,
blit/invalidate and layered-FBO entry points."""

import unittest
from arraycompat import np, object_names

from arraycompat import copy_safe
from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_TEXTURE_2D,
    GL_TEXTURE_3D,
    GL_TEXTURE_2D_ARRAY,
    GL_RENDERBUFFER,
    GL_RGBA8,
    GL_RGBA8I,
    GL_RGBA8UI,
    GL_NUM_SAMPLE_COUNTS,
    GL_COLOR,
    GL_DEPTH_STENCIL,
    GL_FRAMEBUFFER,
    GL_READ_FRAMEBUFFER,
    GL_DRAW_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_NEAREST,
    glGenTextures,
    glBindTexture,
    glTexStorage2D,
    glTexStorage3D,
    glGetInternalformativ,
    glGenRenderbuffers,
    glBindRenderbuffer,
    glRenderbufferStorageMultisample,
    glGenFramebuffers,
    glBindFramebuffer,
    glFramebufferTexture2D,
    glFramebufferTextureLayer,
    glClearBufferfv,
    glClearBufferiv,
    glClearBufferuiv,
    glClearBufferfi,
    glDrawBuffers,
    glReadBuffer,
    glBlitFramebuffer,
    glInvalidateFramebuffer,
    glInvalidateSubFramebuffer,
)


class TestES3FBOStorage(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)
    stencil_size = 8

    def test_immutable_storage(self):
        tex2d = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex2d)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        tex3d = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, tex3d)
        glTexStorage3D(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4)

        counts = np.zeros(1, 'i')
        glGetInternalformativ(
            GL_RENDERBUFFER, GL_RGBA8, GL_NUM_SAMPLE_COUNTS, 1, counts
        )
        self.assertGreaterEqual(int(counts[0]), 0)
        self.check_error('immutable storage')

    def test_multisample_renderbuffer(self):
        rb = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rb)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 4, GL_RGBA8, 16, 16)
        self.check_error('multisample renderbuffer')

    def test_clear_buffers(self):
        glClearBufferfv(GL_COLOR, 0, np.array([0.0, 0.25, 0.0, 1.0], 'f'))
        glClearBufferfi(GL_DEPTH_STENCIL, 0, 1.0, 0)
        self.check_error('clear normalized/depth-stencil')

        # integer colour attachments for the integer clear variants
        for internal, clear, value in (
            (GL_RGBA8I, glClearBufferiv, np.array([1, 2, 3, 4], 'i')),
            (GL_RGBA8UI, glClearBufferuiv, np.array([1, 2, 3, 4], 'u4')),
        ):
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexStorage2D(GL_TEXTURE_2D, 1, internal, 4, 4)
            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0
            )
            glDrawBuffers(1, object_names(GL_COLOR_ATTACHMENT0))
            clear(GL_COLOR, 0, value)
            self.check_error('integer clear')
            glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def test_blit_invalidate_layer(self):
        def color_fbo():
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0
            )
            return fbo

        src = color_fbo()
        dst = color_fbo()
        glBindFramebuffer(GL_READ_FRAMEBUFFER, src)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, dst)
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        glDrawBuffers(1, object_names(GL_COLOR_ATTACHMENT0))
        glBlitFramebuffer(0, 0, 16, 16, 0, 0, 16, 16, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glInvalidateFramebuffer(
                GL_READ_FRAMEBUFFER, 1, copy_safe([GL_COLOR_ATTACHMENT0], 'I')
            )
        glInvalidateSubFramebuffer(
            GL_DRAW_FRAMEBUFFER, 1, copy_safe([GL_COLOR_ATTACHMENT0], 'I'),
            0, 0, 8, 8,
        )
        self.check_error('blit/invalidate')

        # layered attachment from a 2D array texture
        arr = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, arr)
        glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, 16, 16, 2)
        layered = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, layered)
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, arr, 0, 1)
        self.check_error('framebuffer texture layer')
        glBindFramebuffer(GL_FRAMEBUFFER, 0)


if __name__ == '__main__':
    unittest.main()
