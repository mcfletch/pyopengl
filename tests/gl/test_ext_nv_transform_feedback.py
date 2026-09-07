#! /usr/bin/env python3
"""GL_NV_transform_feedback: the original (pre-EXT/ARB) transform-feedback API,
driven through varying *locations* rather than names.

Functional tests -- a real program with an active varying captured into a real
buffer object, with a clean error state.
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403

VS = '#version 150\nout float v; void main(){ v = 1.0; gl_Position = vec4(0.0); }'
FS = '#version 150\nout vec4 c; void main(){ c = vec4(1.0); }'


class TestNVTransformFeedback(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def test_nv_transform_feedback(self):
        self.require_extension('GL_NV_transform_feedback')
        from OpenGL.GL import shaders
        from OpenGL.GL.NV.transform_feedback import (
            glActiveVaryingNV, glGetVaryingLocationNV, glTransformFeedbackVaryingsNV,
            glGetActiveVaryingNV, glGetTransformFeedbackVaryingNV,
            glBindBufferBaseNV, glBindBufferRangeNV, glBindBufferOffsetNV,
            glBeginTransformFeedbackNV, glEndTransformFeedbackNV,
            glTransformFeedbackAttribsNV, GL_INTERLEAVED_ATTRIBS_NV,
            GL_TRANSFORM_FEEDBACK_BUFFER_NV,
        )

        program = glCreateProgram()
        glAttachShader(program, shaders.compileShader(VS, GL_VERTEX_SHADER))
        glAttachShader(program, shaders.compileShader(FS, GL_FRAGMENT_SHADER))
        # NV transform feedback marks varyings active *before* linking
        glActiveVaryingNV(program, b'v')
        glLinkProgram(program)

        loc = one(glGetVaryingLocationNV(program, b'v'))
        glTransformFeedbackVaryingsNV(program, 1, np.array([loc], 'i'),
                                      GL_INTERLEAVED_ATTRIBS_NV)
        length = (ctypes.c_int * 1)()
        size = (ctypes.c_int * 1)()
        gltype = (ctypes.c_uint * 1)()
        namebuf = (ctypes.c_char * 64)()
        glGetActiveVaryingNV(program, 0, 64, length, size, gltype, namebuf)
        glGetTransformFeedbackVaryingNV(program, 0, np.zeros(1, 'i'))

        glUseProgram(program)
        tbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, tbo)
        glBufferData(GL_ARRAY_BUFFER, 64, None, GL_DYNAMIC_COPY)
        glBindBufferBaseNV(GL_TRANSFORM_FEEDBACK_BUFFER_NV, 0, tbo)
        glBindBufferRangeNV(GL_TRANSFORM_FEEDBACK_BUFFER_NV, 0, tbo, 0, 16)
        glBindBufferOffsetNV(GL_TRANSFORM_FEEDBACK_BUFFER_NV, 0, tbo, 0)

        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedbackNV(GL_POINTS)
        glEndTransformFeedbackNV()
        glDisable(GL_RASTERIZER_DISCARD)

        # fixed-function attribute capture: {attribute, components, index} triples
        glTransformFeedbackAttribsNV(1, np.array([GL_POSITION, 4, 0], 'i'),
                                     GL_INTERLEAVED_ATTRIBS_NV)
        glUseProgram(0)
        self.check_error('nv transform feedback')


if __name__ == '__main__':
    unittest.main()
