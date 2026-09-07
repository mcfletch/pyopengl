#! /usr/bin/env python3
"""GLES3.1: program interface query (glGetProgramResource*) entry points."""

import unittest
from arraycompat import np, one

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_UNIFORM,
    GL_PROGRAM_INPUT,
    GL_ACTIVE_RESOURCES,
    GL_TYPE,
    glGetProgramInterfaceiv,
    glGetProgramResourceIndex,
    glGetProgramResourceName,
    glGetProgramResourceiv,
    glGetProgramResourceLocation,
)

VERTEX = '''#version 310 es
in vec4 position;
void main() { gl_Position = position; }'''

FRAGMENT = '''#version 310 es
precision mediump float;
uniform vec4 color;
out vec4 fragColor;
void main() { fragColor = color; }'''


class TestES31ProgramInterface(ESTestCase):
    api = 'gles'
    gl_version = (3, 1)

    def test_program_interface(self):
        program = self.compile_program(VERTEX, FRAGMENT)

        count = np.zeros(1, 'i')
        glGetProgramInterfaceiv(program, GL_UNIFORM, GL_ACTIVE_RESOURCES, count)
        self.assertGreaterEqual(int(count[0]), 1)

        index = glGetProgramResourceIndex(program, GL_UNIFORM, 'color')
        self.assertNotEqual(int(index), 0xFFFFFFFF)

        length, chars = glGetProgramResourceName(program, GL_UNIFORM, index, 64)
        name = bytes(bytearray(int(c) for c in chars[: one(length)])).decode()
        self.assertEqual(name, 'color')

        props = np.array([GL_TYPE], 'I')
        params = np.zeros(1, 'i')
        glGetProgramResourceiv(program, GL_UNIFORM, index, 1, props, 1, None, params)
        self.assertGreater(int(params[0]), 0)

        loc = glGetProgramResourceLocation(program, GL_UNIFORM, 'color')
        self.assertNotEqual(int(loc), -1)

        # also query a program input (the vertex attribute)
        glGetProgramResourceIndex(program, GL_PROGRAM_INPUT, 'position')
        self.check_error('program interface')


if __name__ == '__main__':
    unittest.main()
