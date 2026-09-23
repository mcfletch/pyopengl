#! /usr/bin/env python3
"""``glGetUniformIndices`` answers an index per name the caller asks about.

The entry point takes a count, an array of ``GLchar *`` and a ``GLuint`` array
to write into.  The friendly form takes the names alone: the count is their
number and the answer is the array it returns.

The C ordering is still accepted, for a caller who has built the pointer array
themselves, and the output is allocated for that form too -- which is what the
count is for.
"""

import ctypes
import unittest

from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import (  # noqa: F401
    GL_INVALID_INDEX,
    glGetActiveUniformsiv,
    glGetUniformIndices,
    glUseProgram,
    GL_UNIFORM_OFFSET,
)

VERTEX = '''#version 150 core
in vec4 position;
uniform Block { vec4 blockColor; vec4 blockEdge; float blockWidth; };
void main() {
    gl_Position = position + (blockColor + blockEdge) * blockWidth * 0.0;
}'''
FRAGMENT = '''#version 150 core
out vec4 fragColor;
void main() { fragColor = vec4(1.0); }'''

#: Every uniform the block declares, in the order the cases ask for them.
NAMES = ['blockColor', 'blockEdge', 'blockWidth']


def _char_pp(strings):
    """The ``GLchar *const *`` a caller of the C form builds for themselves."""
    block = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(block, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestUniformIndices(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def setUp(self):
        super().setUp()
        self.program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(self.program)

    def indices(self, *names):
        """What the friendly form answers, as a list of ints."""
        return [int(value) for value in glGetUniformIndices(self.program, list(names))]

    def test_names_as_str(self):
        found = self.indices(*NAMES)
        self.assertEqual(len(found), len(NAMES))
        self.assertEqual(len(set(found)), len(NAMES))
        for index in found:
            self.assertNotEqual(index, GL_INVALID_INDEX)
        self.check_error('names as str')

    def test_names_as_bytes(self):
        """The same answers, for the same names given as bytes."""
        as_bytes = glGetUniformIndices(self.program, [n.encode() for n in NAMES])
        self.assertEqual(
            [int(value) for value in as_bytes], self.indices(*NAMES)
        )
        self.check_error('names as bytes')

    def test_one_name_on_its_own(self):
        """A single string is a list of one, as it is for glShaderSource."""
        answer = glGetUniformIndices(self.program, 'blockColor')
        self.assertEqual(len(answer), 1)
        self.assertEqual(int(answer[0]), self.indices('blockColor')[0])
        self.check_error('one name')

    def test_a_count_the_glget_table_does_not_hold(self):
        """Three names is three indices.

        The output used to be sized by looking the *count* up in the table of
        ``glGet`` sizes, so a count that was not one of those enum values
        raised ``KeyError`` and a count that happened to be one allocated
        whatever that enum's size is -- an array of one, for the driver to
        write three indices into.
        """
        found = self.indices(*NAMES)
        self.assertEqual(len(found), 3)
        self.check_error('three names')

    def test_an_output_array_that_was_passed_in(self):
        """The array given is the array written into and the array returned."""
        given = np.zeros(len(NAMES), 'I')
        answer = glGetUniformIndices(self.program, NAMES, given)
        self.assertEqual(
            [int(value) for value in given], self.indices(*NAMES)
        )
        self.assertEqual([int(value) for value in answer], list(given))
        self.check_error('output passed in')

    def test_an_output_array_by_keyword(self):
        given = np.zeros(len(NAMES), 'I')
        glGetUniformIndices(self.program, NAMES, uniformIndices=given)
        self.assertEqual(
            [int(value) for value in given], self.indices(*NAMES)
        )
        self.check_error('output by keyword')

    def test_a_name_the_program_does_not_declare(self):
        """GL_INVALID_INDEX, rather than an error or a short array."""
        found = glGetUniformIndices(self.program, ['blockColor', 'notThere'])
        self.assertEqual(len(found), 2)
        self.assertNotEqual(int(found[0]), GL_INVALID_INDEX)
        self.assertEqual(int(found[1]), GL_INVALID_INDEX)
        self.check_error('unknown name')

    def test_the_indices_describe_the_block(self):
        """The answers are usable: each names a uniform with a block offset.

        ``glGetActiveUniformsiv`` takes the indices as they come back, which
        is what the wrapper allocates a ``GLuint`` array for.  It writes into
        the ``params`` array the caller provides: its length is
        ``COMPSIZE(uniformCount, pname)`` in the registry, which the
        annotation table has no way to state, so the array is the caller's.
        """
        found = glGetUniformIndices(self.program, NAMES)
        offsets = np.zeros(len(NAMES), 'i')
        glGetActiveUniformsiv(
            self.program, len(NAMES), found, GL_UNIFORM_OFFSET, offsets
        )
        self.assertEqual(len(set(int(value) for value in offsets)), len(NAMES))
        self.check_error('offsets')

    def test_the_c_ordering_still_answers(self):
        """count, prepared pointer array, and an output array of the caller's."""
        given = np.zeros(len(NAMES), 'I')
        glGetUniformIndices(self.program, len(NAMES), _char_pp(NAMES), given)
        self.assertEqual(
            [int(value) for value in given], self.indices(*NAMES)
        )
        self.check_error('C ordering')

    def test_the_c_ordering_allocates_what_the_count_asks_for(self):
        """Without an array of its own, the count says how long the answer is."""
        found = glGetUniformIndices(self.program, len(NAMES), _char_pp(NAMES))
        self.assertEqual(
            [int(value) for value in found], self.indices(*NAMES)
        )
        self.check_error('C ordering, allocated')


class TestBothImportPaths(GLTestCase):
    """GL 3.1 and ARB_uniform_buffer_object are one entry point.

    Both modules declare ``glGetUniformIndices`` and both resolve to the same
    address, so the friendly form has to be the one either import answers with
    -- a caller who imported from the extension is calling the same function.
    """

    profile = 'core'
    gl_version = (3, 3)

    def test_the_two_modules_offer_the_same_wrapper(self):
        from OpenGL.GL.ARB.uniform_buffer_object import glGetUniformIndices as arb
        from OpenGL.GL.VERSION.GL_3_1 import glGetUniformIndices as core

        self.assertIs(arb, core)
        self.assertIs(arb, glGetUniformIndices)

    def test_the_extension_import_takes_the_friendly_call(self):
        from OpenGL.GL.ARB.uniform_buffer_object import glGetUniformIndices as arb

        program = self.compile_program(VERTEX, FRAGMENT)
        glUseProgram(program)
        found = arb(program, NAMES)
        self.assertEqual(len(found), len(NAMES))
        self.assertEqual(
            [int(value) for value in found],
            [int(value) for value in glGetUniformIndices(program, NAMES)],
        )
        self.check_error('ARB import')


if __name__ == '__main__':
    unittest.main()
