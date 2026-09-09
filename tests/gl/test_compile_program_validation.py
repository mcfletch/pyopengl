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
from OpenGL import GL
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

    def test_using_it_as_a_context_manager_hands_back_the_program(self):
        """``with program as bound`` is the point of the context manager.

        The program is the number every later call needs -- glUniform,
        glGetUniformLocation, glUseProgram -- so a ``with`` that binds nothing
        makes the form useless and reads as though it worked.
        """
        program = self.program(ONE_TARGET)
        with program as bound:
            assert bound is program
            assert int(bound) == int(program)

    def test_one_sampler_target_is_still_validated(self):
        """The check is skipped where it cannot mean anything, not removed."""
        program = self.program(ONE_TARGET)
        assert program.validated

    def test_a_link_failure_is_still_reported(self):
        """Skipping validation must not skip the link check with it.

        The vertex shader defines no ``main``, which compiles and cannot link:
        GLSL requires one per stage present, so every driver refuses it.  Two
        sampler targets in the fragment shader as well, so the validation skip
        is in play and the link check is what has to catch this.
        """
        with self.assertRaises(shaders.ShaderLinkError):
            shaders.compileProgram(
                shaders.compileShader(
                    '#version 330 core\n'
                    'void not_main(){ gl_Position = vec4(0.0); }',
                    GL_VERTEX_SHADER,
                ),
                shaders.compileShader(TWO_TARGETS, GL_FRAGMENT_SHADER),
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

    def test_the_skip_is_recorded_rather_than_silent(self):
        """A caller who asked for validation and did not get it has to be able
        to find that out: the answer was withheld, not given."""
        skipped = self.program(TWO_TARGETS)
        assert skipped.validation_deferred is True
        assert skipped.validated is False

        checked = self.program(ONE_TARGET)
        assert checked.validation_deferred is False

    def test_an_explicit_check_clears_the_deferral(self):
        program = self.program(TWO_TARGETS)
        assert program.validation_deferred
        glUseProgram(program)
        glUniform1i(glGetUniformLocation(program, 'colour'), 0)
        glUniform1i(glGetUniformLocation(program, 'table'), 1)
        program.check_validate()
        glUseProgram(0)
        assert program.validation_deferred is False


class TestTheSamplerTypeSet(GLTestCase):
    """``_sampler_types`` describes the GL enums, not this program, so it is a
    property of the module rather than something to work out per link."""

    profile = 'core'
    gl_version = (3, 3)

    def test_it_is_built_once(self):
        first = shaders._sampler_types()
        assert shaders._sampler_types() is first

    def test_it_holds_the_targets_a_shader_declares(self):
        types = shaders._sampler_types()
        for name in (
            'GL_SAMPLER_2D',
            'GL_SAMPLER_CUBE',
            'GL_SAMPLER_2D_SHADOW',
            'GL_SAMPLER_2D_ARRAY',
            'GL_INT_SAMPLER_2D',
            'GL_UNSIGNED_INT_SAMPLER_2D',
        ):
            assert int(getattr(GL, name)) in types, name

    def test_it_holds_no_enum_that_is_not_a_uniform_type(self):
        """``GL_SAMPLER_BINDING`` is a pname and ``GL_SAMPLER`` an object-type
        token; neither is ever a ``glGetActiveUniform`` answer, and a set that
        claims otherwise is one nothing can be reasoned about."""
        types = shaders._sampler_types()
        for name in ('GL_SAMPLER_BINDING', 'GL_SAMPLER', 'GL_MAX_SAMPLES'):
            constant = getattr(GL, name, None)
            if constant is not None:
                assert int(constant) not in types, name


if __name__ == '__main__':
    unittest.main()
