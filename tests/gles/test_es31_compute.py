#! /usr/bin/env python3
"""GLES3.1: compute shader writing to a shader-storage buffer (SSBO).

Dispatches a compute shader that fills an SSBO, then maps the buffer back and
checks the values.
"""

import unittest
import ctypes
import pytest
np = pytest.importorskip('numpy')  # numpy-specific test: skip without numpy

from arraycompat import one
from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_SHADER_STORAGE_BUFFER,
    GL_SHADER_STORAGE_BARRIER_BIT,
    GL_DYNAMIC_DRAW,
    GL_MAP_READ_BIT,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glBindBufferBase,
    glUseProgram,
    glDispatchCompute,
    glMemoryBarrier,
    glMapBufferRange,
    glUnmapBuffer,
)

COUNT = 64
LOCAL_SIZE = 8

COMPUTE_SHADER = '''#version 310 es
layout(local_size_x = 8) in;
layout(std430, binding = 0) buffer Data {
    uint values[];
};
void main() {
    uint i = gl_GlobalInvocationID.x;
    values[i] = i * 2u;
}'''


class TestES31Compute(ESTestCase):
    api = 'gles'
    gl_version = (3, 1)

    def test_compute_ssbo(self):
        program = self.compile_compute(COMPUTE_SHADER)

        size = COUNT * 4
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf)
        glBufferData(
            GL_SHADER_STORAGE_BUFFER, size, np.zeros(COUNT, np.uint32), GL_DYNAMIC_DRAW
        )
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, buf)

        glUseProgram(program)
        glDispatchCompute(COUNT // LOCAL_SIZE, 1, 1)
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)
        self.check_error('dispatch')

        ptr = glMapBufferRange(GL_SHADER_STORAGE_BUFFER, 0, size, GL_MAP_READ_BIT)
        try:
            result = np.frombuffer(
                (ctypes.c_uint32 * COUNT).from_address(
                    ctypes.cast(ptr, ctypes.c_void_p).value
                ),
                dtype=np.uint32,
            ).copy()
        finally:
            glUnmapBuffer(GL_SHADER_STORAGE_BUFFER)

        np.testing.assert_array_equal(result, np.arange(COUNT, dtype=np.uint32) * 2)


if __name__ == '__main__':
    unittest.main()
