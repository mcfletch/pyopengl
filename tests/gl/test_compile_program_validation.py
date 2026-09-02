#! /usr/bin/env python3
"""``compileProgram`` and a program that declares two sampler targets.

Every sampler uniform reads texture image unit 0 until the program is given
its units, and a program is given them after it links.  So a program declaring
a ``sampler2D`` beside a ``samplerBuffer`` -- or beside a shadow sampler, which
is what any lit shader with shadow maps looks like -- sits, the moment it
links, in the state ``glValidateProgram`` is required to reject: "active
samplers with a different type refer to the same texture image unit".

A driver that answers strictly fails it.  Neither answer says anything about
the program, so ``compileProgram`` does not ask at link time, and an explicit
``check_validate()`` still does.
"""

import unittest

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL import shaders

VERTEX = '#version 330 core\nvoid main(){ gl_Position = vec4(0.0); }'

#: Two sampler targets, neither given a unit -- the shape of any shader that
#: reads a texture and something that is not a 2D texture.
TWO_TARGETS = (
    '#version 330 core\n'
    'uniform sampler2D colour;\n'
    'uniform samplerBuffer table;\n'
    'out vec4 frag;\n'
    'void main(){ frag = texture(colour, vec2(0.5)) + texelFetch(table, 0); }'
)

#: One sampler target: nothing for the rule to catch, so validation is asked
#: for and has to pass.
ONE_TARGET = (
    '#version 330 core\n'
    'uniform sampler2D colour;\n'
    'out vec4 frag;\n'
    'void main(){ frag = texture(colour, vec2(0.5)); }'
)


class TestCompileProgramValidation(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def program(self, fragment_source, **named):
        return shaders.compileProgram(
            shaders.compileShader(VERTEX, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_source, GL_FRAGMENT_SHADER),
            **named
        )

    def test_two_sampler_targets_compile(self):
        """What used to raise ShaderValidationError on a strict driver."""
        program = self.program(TWO_TARGETS)
        assert int(program)
        assert glGetProgramiv(program, GL_LINK_STATUS)

    def test_one_sampler_target_is_still_validated(self):
        """The check is skipped where it cannot mean anything, not removed."""
        program = self.program(ONE_TARGET)
        assert program.validated

    def test_a_link_failure_is_still_reported(self):
        """Skipping validation must not skip the link check with it."""
        # The same varying declared with two types: a link error by the rules,
        # not a driver opinion.  Two sampler targets as well, so the skip is in
        # play and the link check is what has to catch it.
        with self.assertRaises(shaders.ShaderLinkError):
            shaders.compileProgram(
                shaders.compileShader(
                    '#version 330 core\nout vec2 shared_varying;\n'
                    'void main(){ shared_varying = vec2(0.0);'
                    ' gl_Position = vec4(0.0); }',
                    GL_VERTEX_SHADER,
                ),
                shaders.compileShader(
                    '#version 330 core\nin vec4 shared_varying;\n'
                    'uniform sampler2D colour;\nuniform samplerBuffer table;\n'
                    'out vec4 f;\n'
                    'void main(){ f = shared_varying + texture(colour, vec2(0.5))'
                    ' + texelFetch(table, 0); }',
                    GL_FRAGMENT_SHADER,
                ),
            )

    def test_an_explicit_check_still_asks(self):
        """A caller who has set its units gets the answer it asked for."""
        program = self.program(TWO_TARGETS)
        glUseProgram(program)
        glUniform1i(glGetUniformLocation(program, 'colour'), 0)
        glUniform1i(glGetUniformLocation(program, 'table'), 1)
        program.check_validate()
        assert program.validated
        glUseProgram(0)

    def test_counting_the_targets(self):
        assert shaders._distinct_sampler_targets(self.program(TWO_TARGETS)) == 2
        assert shaders._distinct_sampler_targets(self.program(ONE_TARGET)) == 1


if __name__ == '__main__':
    unittest.main()
