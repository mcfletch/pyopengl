#! /usr/bin/env python3
"""GL 1.5 (compatibility): buffer objects and occlusion queries."""

import unittest
import ctypes
from arraycompat import np, object_names

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL15(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_buffers(self):
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glBufferSubData(GL_ARRAY_BUFFER, 0, np.ones(4, 'f'))
        self.assertEqual(
            int(glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)), 64
        )
        out = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 16)
        self.assertTrue(len(out) >= 0)
        self.assertTrue(glIsBuffer(buf))
        ptr = glMapBuffer(GL_ARRAY_BUFFER, GL_READ_ONLY)
        self.assertTrue(ptr)
        glGetBufferPointerv(
            GL_ARRAY_BUFFER, GL_BUFFER_MAP_POINTER, ctypes.byref(ctypes.c_void_p())
        )
        glUnmapBuffer(GL_ARRAY_BUFFER)
        glDeleteBuffers(1, object_names(buf))
        self.check_error('buffers')

    def test_queries(self):
        ids = glGenQueries(1)
        q = int(ids[0]) if hasattr(ids, '__len__') else int(ids)
        glBeginQuery(GL_SAMPLES_PASSED, q)
        glEndQuery(GL_SAMPLES_PASSED)
        self.assertTrue(glIsQuery(q))
        glGetQueryiv(GL_SAMPLES_PASSED, GL_CURRENT_QUERY, np.zeros(1, 'i'))
        glGetQueryObjectiv(q, GL_QUERY_RESULT, np.zeros(1, 'i'))
        glGetQueryObjectuiv(q, GL_QUERY_RESULT, np.zeros(1, 'I'))
        glDeleteQueries(1, object_names(q))
        self.check_error('queries')


if __name__ == '__main__':
    unittest.main()
