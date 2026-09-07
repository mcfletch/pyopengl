#! /usr/bin/env python3
"""Legacy NVIDIA assembly-program parameter extensions layered on ARB assembly
programs: NV_gpu_program4 (integer env/local parameters), NV_gpu_program5
(subroutine parameters) and NV_parameter_buffer_object.

Functional tests -- bind a real NVvp4.0 assembly program and drive its integer
parameter state, with a clean error state.
"""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.vertex_program import (
    glGenProgramsARB, glBindProgramARB, glProgramStringARB, glDeleteProgramsARB,
    GL_VERTEX_PROGRAM_ARB, GL_PROGRAM_FORMAT_ASCII_ARB,
)

ASM4 = b'''!!NVvp4.0
MOV result.position, vertex.position;
END'''
T = GL_VERTEX_PROGRAM_ARB


class TestNVARBPrograms(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def _bind_vp4(self):
        prog = one(glGenProgramsARB(1))
        glBindProgramARB(T, prog)
        glProgramStringARB(T, GL_PROGRAM_FORMAT_ASCII_ARB, len(ASM4), ASM4)
        return prog

    def test_nv_gpu_program4(self):
        self.require_extension('GL_NV_gpu_program4')
        from OpenGL.GL.NV.gpu_program4 import (
            glProgramLocalParameterI4iNV, glProgramLocalParameterI4uiNV,
            glProgramLocalParameterI4ivNV, glProgramLocalParameterI4uivNV,
            glProgramLocalParametersI4ivNV, glProgramLocalParametersI4uivNV,
            glProgramEnvParameterI4iNV, glProgramEnvParameterI4uiNV,
            glProgramEnvParameterI4ivNV, glProgramEnvParameterI4uivNV,
            glProgramEnvParametersI4ivNV, glProgramEnvParametersI4uivNV,
            glGetProgramLocalParameterIivNV, glGetProgramLocalParameterIuivNV,
            glGetProgramEnvParameterIivNV, glGetProgramEnvParameterIuivNV,
        )

        self._bind_vp4()
        glProgramLocalParameterI4iNV(T, 0, 1, 2, 3, 4)
        glProgramLocalParameterI4uiNV(T, 1, 1, 2, 3, 4)
        glProgramLocalParameterI4ivNV(T, 0, np.array([1, 2, 3, 4], 'i'))
        glProgramLocalParameterI4uivNV(T, 1, np.array([1, 2, 3, 4], 'u4'))
        glProgramLocalParametersI4ivNV(T, 0, 1, np.array([1, 2, 3, 4], 'i'))
        glProgramLocalParametersI4uivNV(T, 0, 1, np.array([1, 2, 3, 4], 'u4'))
        glProgramEnvParameterI4iNV(T, 0, 1, 2, 3, 4)
        glProgramEnvParameterI4uiNV(T, 1, 1, 2, 3, 4)
        glProgramEnvParameterI4ivNV(T, 0, np.array([1, 2, 3, 4], 'i'))
        glProgramEnvParameterI4uivNV(T, 1, np.array([1, 2, 3, 4], 'u4'))
        glProgramEnvParametersI4ivNV(T, 0, 1, np.array([1, 2, 3, 4], 'i'))
        glProgramEnvParametersI4uivNV(T, 0, 1, np.array([1, 2, 3, 4], 'u4'))
        glGetProgramLocalParameterIivNV(T, 0, np.zeros(4, 'i'))
        glGetProgramLocalParameterIuivNV(T, 1, np.zeros(4, 'u4'))
        glGetProgramEnvParameterIivNV(T, 0, np.zeros(4, 'i'))
        glGetProgramEnvParameterIuivNV(T, 1, np.zeros(4, 'u4'))
        self.check_error('nv gpu program4')

    def test_nv_parameter_buffer_object(self):
        self.require_extension('GL_NV_parameter_buffer_object')
        from OpenGL.GL.NV.parameter_buffer_object import (
            glProgramBufferParametersfvNV, glProgramBufferParametersIivNV,
            glProgramBufferParametersIuivNV, GL_VERTEX_PROGRAM_PARAMETER_BUFFER_NV,
        )

        self._bind_vp4()
        pb = GL_VERTEX_PROGRAM_PARAMETER_BUFFER_NV
        # a buffer must be bound to the parameter-buffer binding point first
        pbuf = one(glGenBuffers(1))
        glBindBufferBase(pb, 0, pbuf)
        glBufferData(pb, 4 * 16, None, GL_DYNAMIC_DRAW)
        glProgramBufferParametersfvNV(pb, 0, 0, 1, np.array([1, 2, 3, 4], 'f'))
        glProgramBufferParametersIivNV(pb, 0, 0, 1, np.array([1, 2, 3, 4], 'i'))
        glProgramBufferParametersIuivNV(pb, 0, 0, 1, np.array([1, 2, 3, 4], 'u4'))
        self.check_error('nv parameter buffer object')

    def test_nv_gpu_program5(self):
        self.require_extension('GL_NV_gpu_program5')
        # Both entry points operate on a program's subroutine-uniform state, which
        # only exists once an NVvp5.0 program declares SUBROUTINE sets and a
        # subroutine uniform; without that the driver returns INVALID_OPERATION.
        # Building such an assembly program is well beyond a state smoke test.
        self.skipTest('subroutine parameters need an NVvp5.0 program with subroutine sets')

    def test_nvx_progress_fence(self):
        self.require_extension('GL_NVX_progress_fence')
        self.skipTest('progress fences signal/wait across external timeline semaphores')


if __name__ == '__main__':
    unittest.main()
