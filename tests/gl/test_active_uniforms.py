#! /usr/bin/env python3
"""The core and ARB spellings of the active-uniform query agree.

``glGetActiveUniform`` and ``glGetActiveUniformARB`` are the same driver
function reached through two generated bindings, and each declares its own
output buffers.  A binding that sized one of them wrongly would answer with a
truncated name or overrun the buffer it was given, and the two spellings are
the pair most likely to drift apart, since one is generated from the core
feature and the other from the extension.
"""

import unittest

from arraycompat import one
from gltestcase import GLTestCase
from OpenGL._scalar import as_int
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.shader_objects import glGetActiveUniformARB
from OpenGL.GL.shaders import compileProgram, compileShader

#: A uniform with a name long enough that a one-byte cap would show, in the
#: fixed-function GLSL the compatibility profile provides.
VERTEX_SHADER = '''#version 120
uniform float scale;
void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex * scale;
}
'''


class TestTheActiveUniformQuery(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def program(self):
        self.require_feature('shaders', (2, 0), 'GL_ARB_shader_objects')
        # Vertex-only, and validate=False with it: a program with no fragment
        # stage fails validation on some drivers, and it is never rendered.
        program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER), validate=False
        )
        self.defer_cleanup(lambda: glDeleteProgram(program))
        return program

    def test_the_core_query_names_the_uniform(self):
        program = self.program()
        count = one(glGetProgramiv(program, GL_ACTIVE_UNIFORMS))
        self.assertGreaterEqual(count, 1, count)
        names = []
        for index in range(count):
            name, size, kind = glGetActiveUniform(program, index)
            names.append(name.decode() if isinstance(name, bytes) else name)
        self.assertIn('scale', names, names)
        self.check_error('glGetActiveUniform')

    def test_the_arb_query_answers_the_same(self):
        """The two bindings are separately generated, so they can disagree."""
        self.require_extension('GL_ARB_shader_objects')
        program = self.program()
        count = one(glGetProgramiv(program, GL_ACTIVE_UNIFORMS))
        for index in range(count):
            core = glGetActiveUniform(program, index)
            arb = glGetActiveUniformARB(program, index)
            self.assertEqual(
                _readable(core), _readable(arb),
                'the core and ARB spellings answered differently for uniform '
                '%d: %r vs %r' % (index, core, arb),
            )
        self.check_error('glGetActiveUniformARB')


def _readable(answer):
    """A multi-output answer as values, whichever shape they arrived in.

    `SIZE_1_ARRAY_UNPACK` decides whether the size and the type come back as
    numbers or as one-element arrays holding them, and two arrays compare by
    identity -- so the two spellings would read as disagreeing whenever they
    agreed.
    """
    return tuple(part if isinstance(part, bytes) else one(part)
                 for part in answer)


class TestEveryOutputOfAMultiOutputQueryIsItsOwn(GLTestCase):
    """A query with several outputs answers about each of them.

    ``glGetActiveUniform`` declares four, and the wrapper collects their
    returns into one object.  Each return knows its argument by name and has
    to be told which index that is; a collection that does not pass the
    telling on leaves every one of them answering about argument zero -- which
    is the program, so the query hands back the program once per output and
    says nothing about the uniform.

    Only reachable with ``SIZE_1_ARRAY_UNPACK`` off, since the unpacking
    return is a different object that carries its own name.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_the_outputs_are_the_name_the_size_and_the_type(self):
        self.require_feature('shaders', (2, 0), 'GL_ARB_shader_objects')
        program = compileProgram(
            compileShader(VERTEX_SHADER, GL_VERTEX_SHADER), validate=False
        )
        found = {}
        for index in range(as_int(glGetProgramiv(program, GL_ACTIVE_UNIFORMS))):
            name, size, kind = glGetActiveUniform(program, index)
            self.assertNotEqual(
                [as_int(size), as_int(kind)], [int(program), int(program)],
                'every output answered with the program: %r'
                % ((name, size, kind),),
            )
            if not isinstance(name, bytes):
                name = bytes(bytearray(name))
            found[name.rstrip(b'\0')] = (as_int(size), as_int(kind))
        # The compatibility profile's built-in uniforms are active too, and
        # which of them the driver lists first is its own business, so the one
        # this program declares is looked for rather than indexed.
        self.assertIn(b'scale', found, sorted(found))
        self.assertEqual(found[b'scale'], (1, GL_FLOAT))
        self.check_error('glGetActiveUniform')


if __name__ == '__main__':
    unittest.main()
