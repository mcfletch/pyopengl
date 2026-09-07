#! /usr/bin/env python3
"""GLES3.2: base-vertex draws, per-draw-buffer blend/colour-mask, indexed
enable, sample shading, tessellation patch and image copy entry points."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_FALSE,
    GL_TRUE,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_BLEND,
    GL_FUNC_ADD,
    GL_FUNC_SUBTRACT,
    GL_ONE,
    GL_ZERO,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_RGBA8,
    GL_FRAMEBUFFER,
    GL_COLOR_ATTACHMENT0,
    glUseProgram,
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glGenTextures,
    glBindTexture,
    glTexStorage2D,
    glGenFramebuffers,
    glBindFramebuffer,
)
from OpenGL.GLES2.ES.VERSION_3_2 import (
    GL_PATCH_VERTICES,
    glDrawElementsBaseVertex,
    glDrawElementsInstancedBaseVertex,
    glDrawRangeElementsBaseVertex,
    glBlendBarrier,
    glBlendFunci,
    glBlendFuncSeparatei,
    glBlendEquationi,
    glBlendEquationSeparatei,
    glColorMaski,
    glEnablei,
    glDisablei,
    glIsEnabledi,
    glMinSampleShading,
    glPatchParameteri,
    glPrimitiveBoundingBox,
    glFramebufferTexture,
    glCopyImageSubData,
)

VERTEX = '''#version 320 es
layout(location = 0) in vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''

FRAGMENT = '''#version 320 es
precision mediump float;
out vec4 fragColor;
void main() { fragColor = vec4( 1.0 ); }'''


class TestES32DrawBlend(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def setUp(self):
        super(TestES32DrawBlend, self).setUp()
        self.program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(self.program)
        self.vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(self.vao))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            48,
            np.array([(-1, -1), (1, -1), (0, 1), (0, 0), (0, 0), (0, 0)], 'f'),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        ebo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER, 12, np.array([0, 1, 2], 'u4'), GL_STATIC_DRAW
        )

    def test_base_vertex_draws(self):
        glDrawElementsBaseVertex(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 0)
        glDrawRangeElementsBaseVertex(GL_TRIANGLES, 0, 2, 3, GL_UNSIGNED_INT, None, 0)
        glDrawElementsInstancedBaseVertex(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2, 0)
        self.check_error('base-vertex draws')

    def test_indexed_blend_and_mask(self):
        glEnablei(GL_BLEND, 0)
        self.assertTrue(glIsEnabledi(GL_BLEND, 0))
        glBlendFunci(0, GL_ONE, GL_ZERO)
        glBlendFuncSeparatei(0, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ZERO)
        glBlendEquationi(0, GL_FUNC_ADD)
        glBlendEquationSeparatei(0, GL_FUNC_ADD, GL_FUNC_SUBTRACT)
        glColorMaski(0, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glBlendBarrier()
        glDisablei(GL_BLEND, 0)
        self.assertFalse(glIsEnabledi(GL_BLEND, 0))
        self.check_error('indexed blend/mask')

    def test_sample_shading_and_patch(self):
        glMinSampleShading(1.0)
        glPatchParameteri(GL_PATCH_VERTICES, 3)
        glPrimitiveBoundingBox(-1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        self.check_error('sample shading / patch')

    def test_framebuffer_texture_and_copy(self):
        src = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, src)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
        dst = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, dst)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 8, 8)
        glCopyImageSubData(
            src, GL_TEXTURE_2D, 0, 0, 0, 0, dst, GL_TEXTURE_2D, 0, 0, 0, 0, 8, 8, 1
        )

        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, src, 0)
        self.check_error('framebuffer texture / copy image')
        glBindFramebuffer(GL_FRAMEBUFFER, 0)


if __name__ == '__main__':
    unittest.main()
