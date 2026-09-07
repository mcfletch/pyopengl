#! /usr/bin/env python3
"""GLES3.1: image load/store, indirect dispatch/draw, framebuffer-without-
attachments, multisample textures, texture-level and vertex-binding state."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_TEXTURE_2D,
    GL_TEXTURE_2D_MULTISAMPLE,
    GL_R32UI,
    GL_RGBA8,
    GL_WRITE_ONLY,
    GL_FALSE,
    GL_TRUE,
    GL_FLOAT,
    GL_INT,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_DISPATCH_INDIRECT_BUFFER,
    GL_DRAW_INDIRECT_BUFFER,
    GL_SHADER_IMAGE_ACCESS_BARRIER_BIT,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_DEFAULT_WIDTH,
    GL_FRAMEBUFFER_DEFAULT_HEIGHT,
    GL_SAMPLE_POSITION,
    GL_TEXTURE_WIDTH,
    GL_SHADER_STORAGE_BUFFER_BINDING,
    GL_COLOR_ATTACHMENT0,
    glFramebufferTexture2D,
    glGenTextures,
    glBindTexture,
    glTexStorage2D,
    glTexStorage2DMultisample,
    glBindImageTexture,
    glUseProgram,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glDispatchComputeIndirect,
    glMemoryBarrierByRegion,
    glGenVertexArrays,
    glBindVertexArray,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glDrawArraysIndirect,
    glDrawElementsIndirect,
    glGenFramebuffers,
    glBindFramebuffer,
    glFramebufferParameteri,
    glGetFramebufferParameteriv,
    glGetMultisamplefv,
    glSampleMaski,
    glGetTexLevelParameteriv,
    glGetTexLevelParameterfv,
    glGetBooleani_v,
    glBindVertexBuffer,
    glVertexAttribFormat,
    glVertexAttribIFormat,
    glVertexAttribBinding,
    glVertexBindingDivisor,
)

COMPUTE = '''#version 310 es
layout(local_size_x = 1) in;
layout(r32ui, binding = 0) uniform highp writeonly uimage2D img;
void main() { imageStore(img, ivec2(gl_GlobalInvocationID.xy), uvec4(42u)); }'''

VERTEX = '''#version 310 es
layout(location = 0) in vec2 position;
void main() { gl_Position = vec4( position, 0.0, 1.0 ); }'''

FRAGMENT = '''#version 310 es
precision mediump float;
out vec4 fragColor;
void main() { fragColor = vec4( 1.0 ); }'''


class TestES31ComputeMisc(ESTestCase):
    api = 'gles'
    gl_version = (3, 1)

    def test_image_and_indirect_dispatch(self):
        program = self.compile_compute(COMPUTE)
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_R32UI, 4, 4)
        glBindImageTexture(0, tex, 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_R32UI)
        glUseProgram(program)

        indirect = one(glGenBuffers(1))
        glBindBuffer(GL_DISPATCH_INDIRECT_BUFFER, indirect)
        glBufferData(
            GL_DISPATCH_INDIRECT_BUFFER, 12, np.array([1, 1, 1], 'u4'), GL_STATIC_DRAW
        )
        glDispatchComputeIndirect(0)
        glMemoryBarrierByRegion(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        self.check_error('image / indirect dispatch')

    def test_indirect_draws(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(vao))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER,
            24,
            np.array([(-1, -1), (1, -1), (0, 1)], 'f'),
            GL_STATIC_DRAW,
        )
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        ebo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(
            GL_ELEMENT_ARRAY_BUFFER, 12, np.array([0, 1, 2], 'u4'), GL_STATIC_DRAW
        )

        indirect = one(glGenBuffers(1))
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, indirect)
        # arrays-indirect: count, instanceCount, first, baseInstance
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, 16, np.array([3, 1, 0, 0], 'u4'), GL_STATIC_DRAW
        )
        glDrawArraysIndirect(GL_TRIANGLES, ctypes.c_void_p(0))
        # elements-indirect: count, instanceCount, firstIndex, baseVertex, baseInstance
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, 20, np.array([3, 1, 0, 0, 0], 'u4'), GL_STATIC_DRAW
        )
        glDrawElementsIndirect(GL_TRIANGLES, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        self.check_error('indirect draws')

    def test_framebuffer_no_attachments(self):
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferParameteri(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_WIDTH, 16)
        glFramebufferParameteri(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_HEIGHT, 16)
        out = np.zeros(1, 'i')
        glGetFramebufferParameteriv(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_WIDTH, out)
        self.assertEqual(int(out[0]), 16)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('framebuffer params')

    def test_multisample_and_levels(self):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, tex)
        glTexStorage2DMultisample(
            GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 16, 16, GL_TRUE
        )
        width = np.zeros(1, 'i')
        glGetTexLevelParameteriv(GL_TEXTURE_2D_MULTISAMPLE, 0, GL_TEXTURE_WIDTH, width)
        self.assertEqual(int(width[0]), 16)
        fwidth = np.zeros(1, 'f')
        glGetTexLevelParameterfv(GL_TEXTURE_2D_MULTISAMPLE, 0, GL_TEXTURE_WIDTH, fwidth)
        glSampleMaski(0, 0xFF)

        # sample-position query needs a bound multisample framebuffer
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, tex, 0
        )
        pos = np.zeros(2, 'f')
        glGetMultisamplefv(GL_SAMPLE_POSITION, 0, pos)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        boolean = np.zeros(1, 'B')
        glGetBooleani_v(GL_SHADER_STORAGE_BUFFER_BINDING, 0, boolean)
        self.check_error('multisample / levels')

    def test_vertex_binding(self):
        vao = one(glGenVertexArrays(1))
        glBindVertexArray(int(vao))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, 64, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glBindVertexBuffer(0, vbo, 0, 16)
        glVertexAttribFormat(0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexAttribIFormat(1, 4, GL_INT, 0)
        glVertexAttribBinding(0, 0)
        glVertexBindingDivisor(0, 1)
        self.check_error('vertex binding')


if __name__ == '__main__':
    unittest.main()
