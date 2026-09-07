#! /usr/bin/env python3
"""GLES3.0: transform feedback capture of a vertex shader's output."""

import unittest
import ctypes
import pytest
np = pytest.importorskip('numpy')  # numpy-specific test: skip without numpy

from arraycompat import object_names
from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_POINTS,
    GL_INTERLEAVED_ATTRIBS,
    GL_TRANSFORM_FEEDBACK,
    GL_TRANSFORM_FEEDBACK_BUFFER,
    GL_RASTERIZER_DISCARD,
    GL_MAP_READ_BIT,
    GL_DYNAMIC_COPY,
    glCreateProgram,
    glAttachShader,
    glLinkProgram,
    glGetProgramiv,
    glUseProgram,
    glTransformFeedbackVaryings,
    glGetTransformFeedbackVarying,
    glGenTransformFeedbacks,
    glBindTransformFeedback,
    glIsTransformFeedback,
    glDeleteTransformFeedbacks,
    glBeginTransformFeedback,
    glEndTransformFeedback,
    glPauseTransformFeedback,
    glResumeTransformFeedback,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glBindBufferBase,
    glGetAttribLocation,
    glEnableVertexAttribArray,
    glVertexAttribPointer,
    glEnable,
    glDisable,
    glDrawArrays,
    glMapBufferRange,
    glUnmapBuffer,
)
from OpenGL.GLES2 import shaders

VERTEX = '''#version 300 es
in float inValue;
out float outValue;
void main() { outValue = inValue * 2.0; }'''

FRAGMENT = '''#version 300 es
precision mediump float;
out vec4 fragColor;
void main() { fragColor = vec4( 1.0 ); }'''


class TestES3TransformFeedback(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_capture(self):
        vs = shaders.compileShader(VERTEX, GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT, GL_FRAGMENT_SHADER)
        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glTransformFeedbackVaryings(program, ['outValue'], GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(program)
        self.assertEqual(glGetProgramiv(program, GL_LINK_STATUS), GL_TRUE)
        glUseProgram(program)

        glGetTransformFeedbackVarying(program, 0, 64)  # introspect the varying

        tfo = glGenTransformFeedbacks(1)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, tfo)
        self.assertTrue(glIsTransformFeedback(tfo))

        src = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, src)
        glBufferData(GL_ARRAY_BUFFER, 12, np.array([1, 2, 3], 'f'), GL_STATIC_DRAW)
        loc = glGetAttribLocation(program, 'inValue')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 1, GL_FLOAT, False, 0, None)

        dst = glGenBuffers(1)
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, dst)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 12, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, dst)

        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_POINTS)
        glPauseTransformFeedback()
        glResumeTransformFeedback()
        glDrawArrays(GL_POINTS, 0, 3)
        glEndTransformFeedback()
        glDisable(GL_RASTERIZER_DISCARD)
        self.check_error('transform feedback')

        ptr = glMapBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER, 0, 12, GL_MAP_READ_BIT)
        try:
            result = np.frombuffer(
                (ctypes.c_float * 3).from_address(
                    ctypes.cast(ptr, ctypes.c_void_p).value
                ),
                dtype='f',
            ).copy()
        finally:
            glUnmapBuffer(GL_TRANSFORM_FEEDBACK_BUFFER)
        np.testing.assert_array_almost_equal(result, [2.0, 4.0, 6.0])

        glDeleteTransformFeedbacks(1, object_names(tfo))


if __name__ == '__main__':
    unittest.main()
