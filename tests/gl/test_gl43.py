#! /usr/bin/env python3
"""GL 4.3 (core): compute, debug, program interface, vertex-attrib binding,
invalidation, copy-image, multi-draw-indirect, texture storage/views."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

COMPUTE = '''#version 430 core
layout(local_size_x=1) in;
layout(std430, binding=0) buffer Data { uint values[]; };
void main() { values[gl_GlobalInvocationID.x] = gl_GlobalInvocationID.x; }'''
VS = '#version 430 core\nin vec4 position; void main(){ gl_Position = position; }'
FS = '#version 430 core\nout vec4 c; void main(){ c = vec4(1.0); }'


class TestGL43(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_compute_and_ssbo(self):
        from OpenGL.GL import shaders

        prog = shaders.compileProgram(shaders.compileShader(COMPUTE, GL_COMPUTE_SHADER))
        glUseProgram(prog)
        ssbo = glGenBuffers(1)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
        glBufferData(GL_SHADER_STORAGE_BUFFER, np.zeros(8, 'I'), GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, ssbo)
        glDispatchCompute(8, 1, 1)
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
        ind = glGenBuffers(1)
        glBindBuffer(GL_DISPATCH_INDIRECT_BUFFER, ind)
        glBufferData(
            GL_DISPATCH_INDIRECT_BUFFER, np.array([1, 1, 1], 'I'), GL_STATIC_DRAW
        )
        glDispatchComputeIndirect(0)
        glMemoryBarrierByRegion(GL_SHADER_STORAGE_BARRIER_BIT)
        self.check_error('compute/ssbo')

    def test_program_interface(self):
        program = self.compile_program(VS, FS)
        glGetProgramInterfaceiv(
            program, GL_PROGRAM_INPUT, GL_ACTIVE_RESOURCES, np.zeros(1, 'i')
        )
        idx = glGetProgramResourceIndex(program, GL_PROGRAM_INPUT, 'position')
        glGetProgramResourceName(program, GL_PROGRAM_INPUT, idx, 64)
        # GLenum, so unsigned: the signed spelling is a conversion the driver
        # never sees and ERROR_ON_COPY refuses.
        props = np.array([GL_TYPE], 'I')
        glGetProgramResourceiv(
            program, GL_PROGRAM_INPUT, idx, 1, props, 1, None, np.zeros(1, 'i')
        )
        glGetProgramResourceLocation(program, GL_PROGRAM_INPUT, 'position')
        glGetProgramResourceLocationIndex(program, GL_PROGRAM_OUTPUT, 'c')
        self.check_error('program interface')

    def test_debug(self):
        with self.exercise():
            captured = []

            @GLDEBUGPROC
            def cb(source, t, i, sev, length, message, user):
                captured.append(1)
                return 0

            self._cb = cb
            glEnable(GL_DEBUG_OUTPUT)
            glDebugMessageCallback(cb, None)
            glDebugMessageControl(
                GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, None, GL_TRUE
            )
            glDebugMessageInsert(
                GL_DEBUG_SOURCE_APPLICATION,
                GL_DEBUG_TYPE_OTHER,
                1,
                GL_DEBUG_SEVERITY_NOTIFICATION,
                -1,
                b'hello',
            )
            glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, b'grp')
            glPopDebugGroup()
            buf = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glObjectLabel(GL_BUFFER, buf, -1, b'lbl')
            glGetObjectLabel(
                GL_BUFFER, buf, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )
            sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
            glObjectPtrLabel(sync, -1, b'sync')
            glGetObjectPtrLabel(sync, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)())
            ptr = ctypes.c_void_p()
            glGetPointerv(GL_DEBUG_CALLBACK_FUNCTION, ctypes.byref(ptr))
            glGetDebugMessageLog(
                4,
                256,
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'i'),
                (ctypes.c_char * 256)(),
            )
            glDeleteSync(sync)

    def test_vertex_attrib_binding(self):
        glBindVertexArray(int(glGenVertexArrays(1)))
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glBindVertexBuffer(0, buf, 0, 16)
        glVertexAttribFormat(0, 4, GL_FLOAT, GL_FALSE, 0)
        glVertexAttribIFormat(1, 4, GL_INT, 0)
        glVertexAttribLFormat(2, 4, GL_DOUBLE, 0)
        glVertexAttribBinding(0, 0)
        glVertexBindingDivisor(0, 1)
        # no-attachment framebuffer: default geometry is settable
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferParameteri(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_WIDTH, 16)
        glFramebufferParameteri(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_HEIGHT, 16)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('vertex attrib binding')

    def test_storage_views_and_misc(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        msa = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, msa)
        glTexStorage2DMultisample(
            GL_TEXTURE_2D_MULTISAMPLE, 4, GL_RGBA8, 16, 16, GL_TRUE
        )
        arr = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE_ARRAY, arr)
        glTexStorage3DMultisample(
            GL_TEXTURE_2D_MULTISAMPLE_ARRAY, 4, GL_RGBA8, 16, 16, 2, GL_TRUE
        )
        view = glGenTextures(1)
        glTextureView(view, GL_TEXTURE_2D, tex, GL_RGBA8, 0, 1, 0, 1)
        buf = glGenBuffers(1)
        glBindBuffer(GL_TEXTURE_BUFFER, buf)
        glBufferData(GL_TEXTURE_BUFFER, np.zeros(64, 'f'), GL_STATIC_DRAW)
        tb = glGenTextures(1)
        glBindTexture(GL_TEXTURE_BUFFER, tb)
        glTexBufferRange(GL_TEXTURE_BUFFER, GL_R32F, buf, 0, 64)
        cp = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, cp)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        glCopyImageSubData(
            tex, GL_TEXTURE_2D, 0, 0, 0, 0, cp, GL_TEXTURE_2D, 0, 0, 0, 0, 16, 16, 1
        )
        glClearBufferData(GL_TEXTURE_BUFFER, GL_R32F, GL_RED, GL_FLOAT, None)
        glClearBufferSubData(GL_TEXTURE_BUFFER, GL_R32F, 0, 64, GL_RED, GL_FLOAT, None)
        glInvalidateTexImage(tex, 0)
        glInvalidateTexSubImage(tex, 0, 0, 0, 0, 16, 16, 1)
        glInvalidateBufferData(buf)
        glInvalidateBufferSubData(buf, 0, 64)
        glGetFramebufferParameteriv(
            GL_DRAW_FRAMEBUFFER, GL_DOUBLEBUFFER, np.zeros(1, 'i')
        )
        glGetInternalformati64v(
            GL_RENDERBUFFER, GL_RGBA8, GL_INTERNALFORMAT_SUPPORTED, 1, np.zeros(1, 'q')
        )
        # program with an SSBO block, for glShaderStorageBlockBinding
        ssbo_fs = (
            '#version 430 core\nlayout(std430, binding=0) buffer B { uint v[]; };\n'
            'out vec4 c; void main(){ c = vec4(float(v[0])); }'
        )
        prog = self.compile_program(VS, ssbo_fs)
        block = glGetProgramResourceIndex(prog, GL_SHADER_STORAGE_BLOCK, 'B')
        glShaderStorageBlockBinding(prog, block, 0)
        glUseProgram(prog)
        # The indirect draws below run this fragment shader, so binding 0 needs
        # a buffer behind it: an active storage block with none leaves the
        # results of shader execution undefined, and the specification allows a
        # driver to interrupt or terminate on it (GL 4.6 core, 7.8 "Shader
        # Buffer Variables and Shader Storage Blocks").
        draw_ssbo = glGenBuffers(1)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, draw_ssbo)
        glBufferData(GL_SHADER_STORAGE_BUFFER, np.zeros(8, 'I'), GL_DYNAMIC_DRAW)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, draw_ssbo)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        ploc = glGetAttribLocation(prog, 'position')
        glEnableVertexAttribArray(ploc)
        glVertexAttribPointer(ploc, 2, GL_FLOAT, False, 0, None)
        ind = glGenBuffers(1)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, ind)
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0], 'I'), GL_STATIC_DRAW
        )
        glMultiDrawArraysIndirect(GL_TRIANGLES, None, 1, 0)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        eind = glGenBuffers(1)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, eind)
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0, 0], 'I'), GL_STATIC_DRAW
        )
        glMultiDrawElementsIndirect(GL_TRIANGLES, GL_UNSIGNED_INT, None, 1, 0)
        glInvalidateFramebuffer(GL_FRAMEBUFFER, 1, np.array([GL_COLOR], 'I'))
        glInvalidateSubFramebuffer(
            GL_FRAMEBUFFER, 1, np.array([GL_COLOR], 'I'), 0, 0, 8, 8
        )
        nfbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, nfbo)
        glFramebufferParameteri(GL_FRAMEBUFFER, GL_FRAMEBUFFER_DEFAULT_WIDTH, 16)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('storage/views/misc')


if __name__ == '__main__':
    unittest.main()
