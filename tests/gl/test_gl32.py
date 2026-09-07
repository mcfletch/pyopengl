#! /usr/bin/env python3
"""GL 3.2 (core): sync objects, base-vertex draws, multisample textures."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

VERTEX = '''#version 150 core
in vec2 position;
void main() { gl_Position = vec4(position, 0.0, 1.0); }'''
FRAGMENT = '''#version 150 core
out vec4 fragColor;
void main() { fragColor = vec4(1.0); }'''


class TestGL32(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_sync(self):
        sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
        self.assertTrue(glIsSync(sync))
        glFlush()
        glClientWaitSync(sync, GL_SYNC_FLUSH_COMMANDS_BIT, 10**8)
        glWaitSync(sync, 0, GL_TIMEOUT_IGNORED)
        glGetSynciv(sync, GL_SYNC_STATUS, 1, np.zeros(1, 'i'), np.zeros(1, 'i'))
        glDeleteSync(sync)
        self.check_error('sync')

    def test_base_vertex_draws(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        glBindVertexArray(one(glGenVertexArrays(1)))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        loc = glGetAttribLocation(program, 'position')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 2, GL_FLOAT, False, 0, None)
        ebo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        glDrawElementsBaseVertex(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 0)
        glDrawRangeElementsBaseVertex(GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, None, 0)
        glDrawElementsInstancedBaseVertex(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2, 0)
        glProvokingVertex(GL_LAST_VERTEX_CONVENTION)
        offsets = (ctypes.c_void_p * 1)(0)  # byte offsets into the bound EBO
        glMultiDrawElementsBaseVertex(
            GL_TRIANGLES,
            np.array([3], 'i'),
            GL_UNSIGNED_INT,
            offsets,
            1,
            np.array([0], 'i'),
        )
        self.check_error('base-vertex draws')

    def test_multisample_textures(self):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, tex)
        glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 16, 16, GL_TRUE)
        arr = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, arr)
        glTexImage3DMultisample(
            GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 16, 16, 2, GL_TRUE
        )
        glSampleMaski(0, 0xFF)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex, 0)
        glGetMultisamplefv(GL_SAMPLE_POSITION, 0, np.zeros(2, 'f'))
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('multisample textures')

    def test_64bit_queries(self):
        # GL_MAX_SERVER_WAIT_TIMEOUT is 3.2's own 64-bit limit, arriving with
        # the sync objects glGetInteger64v was added for.  A 4.3 enum -- which
        # GL_MAX_ELEMENT_INDEX is -- is GL_INVALID_ENUM in the 3.3 context this
        # case asks for, whatever a lenient driver answers.
        glGetInteger64v(GL_MAX_SERVER_WAIT_TIMEOUT)
        glGetInteger64i_v(GL_UNIFORM_BUFFER_BINDING, 0, np.zeros(1, 'q'))
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(4, 'f'), GL_STATIC_DRAW)
        glGetBufferParameteri64v(GL_ARRAY_BUFFER, GL_BUFFER_SIZE, np.zeros(1, 'q'))
        self.check_error('64-bit queries')


if __name__ == '__main__':
    unittest.main()
