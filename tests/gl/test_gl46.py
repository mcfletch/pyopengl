#! /usr/bin/env python3
"""GL 4.6 (core): polygon-offset clamp, SPIR-V specialize, indirect-count draws.

Skipped where the driver tops out below 4.6 / lacks the entry points.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

VS = '#version 460 core\nin vec2 position; void main(){ gl_Position = vec4(position,0,1); }'
FS = '#version 460 core\nout vec4 c; void main(){ c = vec4(1.0); }'


class TestGL46(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_polygon_offset_clamp(self):
        with self.allow_missing():
            glPolygonOffsetClamp(1.0, 1.0, 0.0)
            self.check_error('polygon offset clamp')

    def test_indirect_count(self):
        self.require_version(4, 6)
        with self.allow_missing():
            program = self.compile_program(VS, FS)
            glUseProgram(program)
            vbo = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(
                GL_ARRAY_BUFFER,
                np.array([(-1, -1), (1, -1), (0, 1)], 'f'),
                GL_STATIC_DRAW,
            )
            # An indexed draw reads its indices from a bound element array
            # buffer, and generates INVALID_OPERATION where none is.
            ebo = one(glGenBuffers(1))
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(
                GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW
            )
            ind = one(glGenBuffers(1))
            glBindBuffer(GL_DRAW_INDIRECT_BUFFER, ind)
            # Five uints: DrawArraysIndirect reads the first four (count,
            # primCount, first, baseInstance) and DrawElementsIndirect all
            # five (count, primCount, firstIndex, baseVertex, baseInstance),
            # so one buffer serves both draws.
            glBufferData(
                GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0, 0], 'I'), GL_STATIC_DRAW
            )
            cnt = one(glGenBuffers(1))
            glBindBuffer(GL_PARAMETER_BUFFER, cnt)
            glBufferData(GL_PARAMETER_BUFFER, np.array([1], 'I'), GL_STATIC_DRAW)
            glMultiDrawArraysIndirectCount(GL_TRIANGLES, ctypes.c_void_p(0), 0, 1, 0)
            glMultiDrawElementsIndirectCount(
                GL_TRIANGLES, GL_UNSIGNED_INT, ctypes.c_void_p(0), 0, 1, 0
            )
            self.check_error('indirect count')

    def test_specialize_shader(self):
        self.require_version(4, 6)
        # no SPIR-V blob loaded, so specialization fails; the call still drives
        # the wrapper (entry name -> uint arrays) and exercise() tolerates it
        with self.exercise():
            sh = glCreateShader(GL_VERTEX_SHADER)
            glSpecializeShader(sh, b'main', 0, np.zeros(0, 'I'), np.zeros(0, 'I'))


if __name__ == '__main__':
    unittest.main()
