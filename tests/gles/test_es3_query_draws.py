#! /usr/bin/env python3
"""GLES3.0: occlusion queries, instanced/ranged drawing, buffer copy/query."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_COPY_WRITE_BUFFER,
    GL_STATIC_DRAW,
    GL_BUFFER_SIZE,
    GL_BUFFER_MAP_POINTER,
    GL_MAP_WRITE_BIT,
    GL_MAP_FLUSH_EXPLICIT_BIT,
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_ANY_SAMPLES_PASSED,
    GL_CURRENT_QUERY,
    GL_QUERY_RESULT,
    glUseProgram,
    glGetAttribLocation,
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glVertexAttribDivisor,
    glDrawArraysInstanced,
    glDrawElementsInstanced,
    glDrawRangeElements,
    glGenQueries,
    glBeginQuery,
    glEndQuery,
    glGetQueryiv,
    glGetQueryObjectuiv,
    glIsQuery,
    glDeleteQueries,
    glCopyBufferSubData,
    glGetBufferParameteri64v,
    glGetBufferPointerv,
    glMapBufferRange,
    glFlushMappedBufferRange,
    glUnmapBuffer,
)

VERTEX = '''#version 300 es
layout(location = 0) in vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''

FRAGMENT = '''#version 300 es
precision mediump float;
out vec4 fragColor;
void main() { fragColor = vec4( 1.0 ); }'''


class TestES3QueryDraws(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def setUp(self):
        super(TestES3QueryDraws, self).setUp()
        self.program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(self.program)
        self.vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(self.vao))
        self.vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            24,
            np.array([(-1, -1), (1, -1), (0, 1)], 'f'),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        self.ebo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER,
            12,
            np.array([0, 1, 2], np.uint32),
            GL_STATIC_DRAW,
        )

    def test_queries_and_instanced(self):
        query = one(glGenQueries(1))
        glBeginQuery(GL_ANY_SAMPLES_PASSED, query)
        glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 2)
        glDrawElementsInstanced(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2)
        glDrawRangeElements(GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, None)
        glVertexAttribDivisor(0, 0)
        glEndQuery(GL_ANY_SAMPLES_PASSED)
        self.assertTrue(glIsQuery(query))

        cur = np.zeros(1, 'i')
        glGetQueryiv(GL_ANY_SAMPLES_PASSED, GL_CURRENT_QUERY, cur)
        result = np.zeros(1, 'u4')
        glGetQueryObjectuiv(query, GL_QUERY_RESULT, result)
        self.check_error('queries')
        glDeleteQueries(1, object_names(query))

    def test_buffer_copy_and_query(self):
        dst = one(glGenBuffers(1))
        glBindBuffer(GL_COPY_WRITE_BUFFER, dst)
        glBufferData(GL_COPY_WRITE_BUFFER, 24, None, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glCopyBufferSubData(GL_ARRAY_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0, 24)

        size64 = np.zeros(1, 'q')
        glGetBufferParameteri64v(GL_ARRAY_BUFFER, GL_BUFFER_SIZE, size64)
        self.assertEqual(int(size64[0]), 24)
        pointer = ctypes.c_void_p()
        glGetBufferPointerv(
            GL_ARRAY_BUFFER, GL_BUFFER_MAP_POINTER, ctypes.byref(pointer)
        )
        self.check_error('buffer copy/query')

    def test_flush_mapped_range(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        ptr = glMapBufferRange(
            GL_ARRAY_BUFFER, 0, 24, GL_MAP_WRITE_BIT | GL_MAP_FLUSH_EXPLICIT_BIT
        )
        self.assertTrue(ptr)
        glFlushMappedBufferRange(GL_ARRAY_BUFFER, 0, 24)
        glUnmapBuffer(GL_ARRAY_BUFFER)
        self.check_error('flush mapped range')


if __name__ == '__main__':
    unittest.main()
