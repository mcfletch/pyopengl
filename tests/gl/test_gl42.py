#! /usr/bin/env python3
"""GL 4.2 (core): image load/store, memory barrier, immutable storage,
base-instance draws, internal-format queries."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


VS = '#version 420 core\nin vec2 position; void main(){ gl_Position = vec4(position,0,1); }'
FS = '#version 420 core\nout vec4 c; void main(){ c = vec4(1.0); }'


class TestGL42(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_storage_and_image(self):
        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, 16, 16)
        tex1 = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_1D, tex1)
        glTexStorage1D(GL_TEXTURE_1D, 1, GL_RGBA8, 16)
        tex3 = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_3D, tex3)
        glTexStorage3D(GL_TEXTURE_3D, 1, GL_RGBA8, 4, 4, 4)
        glBindImageTexture(0, tex, 0, GL_FALSE, 0, GL_READ_WRITE, GL_RGBA8)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        counts = np.zeros(1, 'i')
        glGetInternalformativ(
            GL_RENDERBUFFER, GL_RGBA8, GL_NUM_SAMPLE_COUNTS, 1, counts
        )
        self.check_error('storage/image')

    def test_base_instance_draws(self):
        program = self.compile_program(VS, FS)
        glUseProgram(program)
        glBindVertexArray(one(glGenVertexArrays(1)))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        loc = glGetAttribLocation(program, 'position')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 2, GL_FLOAT, False, 0, None)
        ebo = one(glGenBuffers(1))
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        glDrawArraysInstancedBaseInstance(GL_TRIANGLES, 0, 3, 1, 0)
        glDrawElementsInstancedBaseInstance(
            GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 1, 0
        )
        glDrawElementsInstancedBaseVertexBaseInstance(
            GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 1, 0, 0
        )
        self.check_error('base-instance draws')

    def test_transform_feedback_instanced(self):
        from OpenGL.GL import shaders

        fb = glCreateProgram()
        glAttachShader(
            fb,
            shaders.compileShader(
                '#version 420 core\nin vec4 position; out vec4 vout;\nvoid main(){ vout = position; gl_Position = position; }',
                GL_VERTEX_SHADER,
            ),
        )
        glAttachShader(
            fb,
            shaders.compileShader(
                '#version 420 core\nout vec4 c; void main(){ c = vec4(1.0); }',
                GL_FRAGMENT_SHADER,
            ),
        )
        glTransformFeedbackVaryings(fb, 1, _char_pp(['vout']), GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(fb)
        glUseProgram(fb)
        glBindVertexArray(one(glGenVertexArrays(1)))
        vbo = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        ploc = glGetAttribLocation(fb, 'position')
        glEnableVertexAttribArray(ploc)
        glVertexAttribPointer(ploc, 2, GL_FLOAT, False, 0, None)
        tfo = one(glGenTransformFeedbacks(1))
        tfo = int(tfo[0]) if hasattr(tfo, '__len__') else int(tfo)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, tfo)
        tbuf = one(glGenBuffers(1))
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, tbuf)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 256, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbuf)
        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_TRIANGLES)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glEndTransformFeedback()
        glDisable(GL_RASTERIZER_DISCARD)
        glDrawTransformFeedbackInstanced(GL_TRIANGLES, tfo, 2)
        glDrawTransformFeedbackStreamInstanced(GL_TRIANGLES, tfo, 0, 2)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, 0)
        self.check_error('transform feedback instanced')

    def test_active_atomic_counter_buffer(self):
        prog = self.compile_program(
            '#version 420 core\nin vec4 position; void main(){ gl_Position = position; }',
            '#version 420 core\nlayout(binding=0, offset=0) uniform atomic_uint ac;\n'
            'out vec4 c; void main(){ atomicCounterIncrement(ac); c = vec4(1.0); }',
        )
        glGetActiveAtomicCounterBufferiv(
            prog, 0, GL_ATOMIC_COUNTER_BUFFER_DATA_SIZE, np.zeros(1, 'i')
        )
        self.check_error('active atomic counter buffer')


if __name__ == '__main__':
    unittest.main()
