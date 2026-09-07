#! /usr/bin/env python3
"""Drawing extensions: base-vertex/base-instance/instanced/multi-draw variants.

Each extension is independently gated with require_extension + allow_missing, so
it runs where the driver exports the entry points and skips otherwise.
"""

import unittest
import ctypes
from arraycompat import np, object_names

from egltestcase import ESTestCase
from OpenGL.GLES3 import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_FALSE,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_COLOR_ATTACHMENT0,
    glUseProgram,
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
)
from OpenGL.GLES2.EXT import base_instance, draw_elements_base_vertex, draw_instanced
from OpenGL.GLES2.EXT import instanced_arrays, multi_draw_arrays, multi_draw_indirect
from OpenGL.GLES2.OES import draw_elements_base_vertex as oes_debv
from OpenGL.GLES2.NV import draw_buffers as nv_draw_buffers

VERTEX = '''#version 300 es
layout(location = 0) in vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''
FRAGMENT = '''#version 300 es
precision mediump float;
out vec4 c; void main() { c = vec4( 1.0 ); }'''


class TestDrawExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def setUp(self):
        super(TestDrawExtensions, self).setUp()
        glUseProgram(self.compile_program(VERTEX, FRAGMENT))
        glBindVertexArray(int(glGenVertexArrays(1)))
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            24,
            np.array([(-1, -1), (1, -1), (0, 1)], 'f'),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER, 12, np.array([0, 1, 2], 'u4'), GL_STATIC_DRAW
        )

    def test_ext_draw_instanced(self):
        self.require_extension('GL_EXT_draw_instanced')
        with self.exercise():
            draw_instanced.glDrawArraysInstancedEXT(GL_TRIANGLES, 0, 3, 2)
            draw_instanced.glDrawElementsInstancedEXT(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2
            )
            self.check_error('draw_instanced')

    def test_ext_instanced_arrays(self):
        self.require_extension('GL_EXT_instanced_arrays')
        with self.exercise():
            instanced_arrays.glVertexAttribDivisorEXT(0, 0)
            instanced_arrays.glDrawArraysInstancedEXT(GL_TRIANGLES, 0, 3, 2)
            self.check_error('instanced_arrays')

    def test_ext_base_instance(self):
        self.require_extension('GL_EXT_base_instance')
        with self.exercise():
            base_instance.glDrawArraysInstancedBaseInstanceEXT(GL_TRIANGLES, 0, 3, 1, 0)
            base_instance.glDrawElementsInstancedBaseInstanceEXT(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 1, 0
            )
            base_instance.glDrawElementsInstancedBaseVertexBaseInstanceEXT(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 1, 0, 0
            )
            self.check_error('base_instance')

    def test_ext_draw_elements_base_vertex(self):
        self.require_extension('GL_EXT_draw_elements_base_vertex')
        with self.exercise():
            draw_elements_base_vertex.glDrawElementsBaseVertexEXT(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 0
            )
            draw_elements_base_vertex.glDrawRangeElementsBaseVertexEXT(
                GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, None, 0
            )
            draw_elements_base_vertex.glDrawElementsInstancedBaseVertexEXT(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2, 0
            )
            self.check_error('draw_elements_base_vertex')

    def test_oes_draw_elements_base_vertex(self):
        self.require_extension('GL_OES_draw_elements_base_vertex')
        with self.exercise():
            oes_debv.glDrawElementsBaseVertexOES(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 0
            )
            oes_debv.glDrawRangeElementsBaseVertexOES(
                GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, None, 0
            )
            oes_debv.glDrawElementsInstancedBaseVertexOES(
                GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2, 0
            )
            self.check_error('oes base vertex')

    def test_ext_multi_draw_arrays(self):
        self.require_extension('GL_EXT_multi_draw_arrays')
        with self.exercise():
            firsts = np.array([0], 'i')
            counts = np.array([3], 'i')
            multi_draw_arrays.glMultiDrawArraysEXT(GL_TRIANGLES, firsts, counts, 1)
            self.check_error('multi_draw_arrays')

    def test_ext_multi_draw_indirect(self):
        self.require_extension('GL_EXT_multi_draw_indirect')
        with self.exercise():
            from OpenGL.GLES3 import GL_DRAW_INDIRECT_BUFFER

            indirect = glGenBuffers(1)
            glBindBuffer(GL_DRAW_INDIRECT_BUFFER, indirect)
            glBufferData(
                GL_DRAW_INDIRECT_BUFFER,
                16,
                np.array([3, 1, 0, 0], 'u4'),
                GL_STATIC_DRAW,
            )
            multi_draw_indirect.glMultiDrawArraysIndirectEXT(
                GL_TRIANGLES, ctypes.c_void_p(0), 1, 0
            )
            self.check_error('multi_draw_indirect')

    def test_nv_draw_buffers(self):
        self.require_extension('GL_NV_draw_buffers')
        with self.exercise():
            nv_draw_buffers.glDrawBuffersNV(1, object_names(GL_COLOR_ATTACHMENT0))
            self.check_error('nv_draw_buffers')


if __name__ == '__main__':
    unittest.main()
