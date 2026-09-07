#! /usr/bin/env python3
"""GL 4.4 (core): immutable buffer storage, texture clears, multi-bind."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.raw.GL import _types


def _ssize(*vals):
    return (ctypes.c_ssize_t * len(vals))(*vals)


class TestGL44(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_buffer_storage_and_clear(self):
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferStorage(
            GL_ARRAY_BUFFER, 64, None, GL_MAP_READ_BIT | GL_DYNAMIC_STORAGE_BIT
        )
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        glClearTexImage(tex, 0, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros(4, 'B'))
        glClearTexSubImage(
            tex, 0, 0, 0, 0, 8, 8, 1, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros(4, 'B')
        )
        self.check_error('storage/clear')

    def test_multi_bind(self):
        glBindVertexArray(one(glGenVertexArrays(1)))
        bufs = glGenBuffers(2)
        ids = np.array([int(b) for b in bufs], 'I')
        for b in ids:
            glBindBuffer(GL_UNIFORM_BUFFER, int(b))
            glBufferData(GL_UNIFORM_BUFFER, 64, None, GL_STATIC_DRAW)
        glBindBuffersBase(GL_UNIFORM_BUFFER, 0, 2, ids)
        # GLintptr*/GLsizeiptr* args need ctypes arrays (numpy not accepted).
        # Built from the declared types rather than a fixed ctypes one: both
        # are pointer-sized, which c_ulong is only where long is.
        glBindBuffersRange(
            GL_UNIFORM_BUFFER,
            0,
            2,
            ids,
            (_types.GLintptr * 2)(0, 0),
            (_types.GLsizeiptr * 2)(64, 64),
        )
        texs = np.array([int(t) for t in glGenTextures(2)], 'I')
        for t in texs:
            glBindTexture(GL_TEXTURE_2D, int(t))
            glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 4, 4)
        glBindTextures(0, 2, texs)
        samplers = np.array([int(s) for s in glGenSamplers(2)], 'I')
        glBindSamplers(0, 2, samplers)
        glBindImageTextures(0, 2, texs)
        vbufs = glGenBuffers(2)
        vids = np.array([int(b) for b in vbufs], 'I')
        for b in vids:
            glBindBuffer(GL_ARRAY_BUFFER, int(b))
            glBufferData(GL_ARRAY_BUFFER, 64, None, GL_STATIC_DRAW)
        glBindVertexBuffers(
            0, 2, vids, (_types.GLintptr * 2)(0, 0), (_types.GLsizei * 2)(16, 16)
        )
        self.check_error('multi bind')


if __name__ == '__main__':
    unittest.main()
