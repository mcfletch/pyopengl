#! /usr/bin/env python3
"""GLES2: texture parameters, buffer objects, renderbuffers and FBO queries."""

import unittest
from arraycompat import np, object_names

from arraycompat import copy_safe
from egltestcase import ESTestCase

from OpenGL.GLES2 import (
    GL_TEXTURE_2D,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_NEAREST,
    GL_LINEAR,
    GL_CLAMP_TO_EDGE,
    GL_RGBA,
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_BUFFER_SIZE,
    GL_RENDERBUFFER,
    GL_RGBA4,
    GL_RENDERBUFFER_WIDTH,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE,
    glGenTextures,
    glBindTexture,
    glIsTexture,
    glDeleteTextures,
    glTexParameterf,
    glTexParameteri,
    glTexParameterfv,
    glTexParameteriv,
    glGetTexParameterfv,
    glGetTexParameteriv,
    glCopyTexImage2D,
    glCopyTexSubImage2D,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glBufferSubData,
    glGetBufferParameteriv,
    glIsBuffer,
    glDeleteBuffers,
    glGenRenderbuffers,
    glBindRenderbuffer,
    glRenderbufferStorage,
    glGetRenderbufferParameteriv,
    glIsRenderbuffer,
    glDeleteRenderbuffers,
    glGenFramebuffers,
    glBindFramebuffer,
    glFramebufferRenderbuffer,
    glGetFramebufferAttachmentParameteriv,
    glIsFramebuffer,
    glDeleteFramebuffers,
)


class TestES2TexBuffers(ESTestCase):
    api = 'gles'
    gl_version = (2, 0)

    def test_texture_parameters(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, float(GL_LINEAR))
        glTexParameterfv(
            GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
            copy_safe([float(GL_CLAMP_TO_EDGE)], 'f'),
        )
        glTexParameteriv(
            GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,
            copy_safe([int(GL_CLAMP_TO_EDGE)], 'i'),
        )
        self.assertEqual(
            int(glGetTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER)),
            int(GL_NEAREST),
        )
        self.assertEqual(
            int(glGetTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER)),
            int(GL_LINEAR),
        )
        self.assertTrue(glIsTexture(tex))

        # copy from the (cleared) framebuffer into the bound texture
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 0, 0, 16, 16, 0)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, 8, 8)
        self.check_error('texture')
        glDeleteTextures(1, object_names(tex))

    def test_buffers(self):
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glBufferSubData(GL_ARRAY_BUFFER, 0, 16, np.ones(4, 'f'))
        self.assertEqual(
            int(glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)), 64
        )
        self.assertTrue(glIsBuffer(buf))
        self.check_error('buffers')
        glDeleteBuffers(1, object_names(buf))
        self.assertFalse(glIsBuffer(buf))

    def test_friendly_buffer_and_delete_forms(self):
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)  # no size
        glBufferSubData(GL_ARRAY_BUFFER, 0, np.ones(4, 'f'))  # no size
        self.assertEqual(
            int(glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)), 64
        )
        glDeleteBuffers(object_names(buf))  # no count
        self.assertFalse(glIsBuffer(buf))

        tex = glGenTextures(2)
        glDeleteTextures(tex)  # no count
        self.check_error('friendly forms')

    def test_renderbuffer_and_fbo(self):
        rb = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rb)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA4, 16, 16)
        self.assertEqual(
            int(glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_WIDTH)),
            16,
        )
        self.assertTrue(glIsRenderbuffer(rb))

        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rb
        )
        glGetFramebufferAttachmentParameteriv(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE
        )
        self.assertTrue(glIsFramebuffer(fbo))
        self.check_error('renderbuffer/fbo')

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDeleteFramebuffers(1, object_names(fbo))
        glDeleteRenderbuffers(1, object_names(rb))


if __name__ == '__main__':
    unittest.main()
