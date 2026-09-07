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
                tuple(core), tuple(arb),
                'the core and ARB spellings answered differently for uniform '
                '%d: %r vs %r' % (index, core, arb),
            )
        self.check_error('glGetActiveUniformARB')


if __name__ == '__main__':
    unittest.main()
