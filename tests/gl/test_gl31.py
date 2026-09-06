#! /usr/bin/env python3
"""GL 3.1 (core): uniform blocks, instancing, buffer copy, texture buffer."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

VERTEX = '''#version 150 core
in vec4 position;
uniform Block { vec4 blockColor; };
void main() { gl_Position = position + blockColor * 0.0; }'''
#: The same shader without the uniform block, for the cases that draw.
#:
#: An active uniform block with no buffer object bound to its binding point
#: leaves the results of shader execution undefined, and the GL specification
#: allows a driver to interrupt or terminate on it (GL 3.3 core, 2.14.3
#: "Uniform Variables"; GL 4.6 core, 7.6.3).  A case whose subject is
#: instancing has no reason to spend that: it draws with a program that
#: declares no block, and ``test_uniform_blocks`` keeps the block and backs it.
PLAIN_VERTEX = '''#version 150 core
in vec4 position;
void main() { gl_Position = position; }'''
FRAGMENT = '''#version 150 core
out vec4 fragColor;
void main() { fragColor = vec4(1.0); }'''


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestGL31(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_uniform_blocks(self):
        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        index = glGetUniformBlockIndex(program, 'Block')
        self.assertNotEqual(index, GL_INVALID_INDEX)
        glGetActiveUniformBlockiv(
            program, index, GL_UNIFORM_BLOCK_DATA_SIZE, np.zeros(1, 'i')
        )
        glGetActiveUniformBlockName(program, index, 64)
        glUniformBlockBinding(program, index, 0)
        names = _char_pp(['blockColor'])
        indices = np.zeros(1, 'I')
        glGetUniformIndices(program, 1, names, indices)
        glGetActiveUniformsiv(program, 1, indices, GL_UNIFORM_TYPE, np.zeros(1, 'i'))
        glGetActiveUniformName(program, int(indices[0]), 64)
        ubo = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, ubo)
        glBufferData(GL_UNIFORM_BUFFER, np.ones(4, 'f'), GL_STATIC_DRAW)
        glBindBufferBase(GL_UNIFORM_BUFFER, 0, ubo)
        glBindBufferRange(GL_UNIFORM_BUFFER, 0, ubo, 0, 16)
        glGetIntegeri_v(GL_UNIFORM_BUFFER_BINDING, 0, np.zeros(1, 'i'))
        self.check_error('uniform blocks')

    def test_instanced_and_copy(self):
        program = self.compile_program(PLAIN_VERTEX, FRAGMENT)
        glUseProgram(program)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        loc = glGetAttribLocation(program, 'position')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 2, GL_FLOAT, False, 0, None)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        glDrawArraysInstanced(GL_TRIANGLES, 0, 3, 2)
        glDrawElementsInstanced(GL_TRIANGLES, 3, GL_UNSIGNED_INT, None, 2)
        dst = glGenBuffers(1)
        glBindBuffer(GL_COPY_WRITE_BUFFER, dst)
        glBufferData(GL_COPY_WRITE_BUFFER, 24, None, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glCopyBufferSubData(GL_ARRAY_BUFFER, GL_COPY_WRITE_BUFFER, 0, 0, 24)
        glPrimitiveRestartIndex(0xFFFFFFFF)
        self.check_error('instanced/copy')

    def test_texture_buffer(self):
        buf = glGenBuffers(1)
        glBindBuffer(GL_TEXTURE_BUFFER, buf)
        glBufferData(GL_TEXTURE_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_BUFFER, tex)
        glTexBuffer(GL_TEXTURE_BUFFER, GL_R32F, buf)
        self.check_error('texture buffer')


if __name__ == '__main__':
    unittest.main()
