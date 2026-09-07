#! /usr/bin/env python3
"""The entry points that take an array of strings accept the same forms.

``glShaderSource``, ``glTransformFeedbackVaryings`` and their neighbours are
declared as ``GLchar *const *``: an array of pointers to nul-terminated
strings.  What a caller may hand over for one is a ``str``, ``bytes`` or
``bytearray``, a sequence of those, or a pointer array they built themselves --
and which of them work must not depend on whether the compiled dispatch layer
is installed, because a program written on a machine with it has to run on a
machine without it.

The hand-written C entry points are asserted to still *be* the C entry points:
they exist to do this work in C, and a friendly module that rebuilds the
binding must not put the ctypes wrapper back over the top.
"""

import ctypes
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL import _dispatch

#: What refusing a bad argument raises.  The C layer raises the ``TypeError``
#: its conversion raised; the ctypes bindings hand the same refusal back inside
#: ``ctypes.ArgumentError``, which is what ctypes does with anything a
#: ``from_param`` or a converter raises.
REFUSED = (TypeError, ValueError, ctypes.ArgumentError)

VERTEX_120 = 'void main() { gl_Position = vec4(0.0, 0.0, 0.0, 1.0); }'

#: A vertex shader with a uniform and an out, for the queries that need one.
VERTEX_150 = '''#version 150 core
in vec2 position;
uniform vec4 tint;
out vec4 carried;
void main() {
    carried = tint;
    gl_Position = vec4(position, 0.0, 1.0);
}'''

FRAGMENT_150 = '''#version 150 core
in vec4 carried;
out vec4 fragColor;
void main() { fragColor = carried; }'''


class TestShaderSourceForms(GLTestCase):
    """``glShaderSource(shader, string)`` takes the string however it comes."""

    profile = 'compat'
    gl_version = (2, 0)

    def setUp(self):
        super().setUp()
        self.shader = glCreateShader(GL_VERTEX_SHADER)
        self.addCleanup(glDeleteShader, self.shader)

    def compiles(self, source):
        glShaderSource(self.shader, source)
        glCompileShader(self.shader)
        assert glGetShaderiv(self.shader, GL_COMPILE_STATUS) == GL_TRUE, (
            glGetShaderInfoLog(self.shader)
        )

    def test_one_string(self):
        self.compiles(VERTEX_120)

    def test_one_bytes(self):
        self.compiles(VERTEX_120.encode())

    def test_a_list_of_strings(self):
        self.compiles(['void main() {\n', '  gl_Position = vec4(0.0);\n', '}\n'])

    def test_a_tuple_of_bytes(self):
        self.compiles((b'void main() {\n', b'  gl_Position = vec4(0.0);\n', b'}\n'))

    def test_one_bytearray(self):
        """A buffer assembled a piece at a time is the bytes it holds."""
        self.compiles(bytearray(VERTEX_120.encode()))

    def test_a_list_of_bytearrays(self):
        self.compiles([bytearray(b'void main() {\n'), bytearray(b'}\n')])

    def test_a_source_that_is_not_a_string_is_refused(self):
        """Rendering it would compile ``42`` as GLSL and report a shader error.

        The implementations differ in which exception carries that, because
        ctypes wraps what a conversion raises in its own ``ArgumentError``;
        both refuse, and both name the offending item.
        """
        with pytest.raises(REFUSED) as raised:
            glShaderSource(self.shader, ['void main(){}', 42])
        assert 'int' in str(raised.value)

    def test_the_source_reads_back(self):
        """What the driver was given is what the caller passed."""
        glShaderSource(self.shader, VERTEX_120)
        assert glGetShaderSource(self.shader).strip() == VERTEX_120.encode()


@pytest.mark.skipif(
    not _dispatch.AVAILABLE, reason='the C dispatch extension is not built'
)
class TestTheHandWrittenEntryPointsAreUsed(GLTestCase):
    """A hand-written C entry point stays the implementation.

    ``OpenGL.GL.VERSION.GL_2_0`` rebuilds ``glShaderSource`` from scratch and
    describes the two arguments its friendly form drops.  The C form already
    takes the friendly two, so the description restates what the C does -- and
    a restatement must leave the C entry point in place rather than demote it
    to the ctypes wrapper it exists to replace.
    """

    profile = 'compat'
    gl_version = (2, 0)

    def setUp(self):
        super().setUp()
        if not _dispatch.ACTIVE:
            self.skipTest('PYOPENGL_DISPATCH=c selects the implementation under test')

    def is_c_entry_point(self, function):
        from OpenGL_accelerate import dispatch

        return isinstance(function, dispatch.GLProc)

    def test_glShaderSource_is_the_c_entry_point(self):
        assert self.is_c_entry_point(glShaderSource)

    def test_glShaderSourceARB_is_the_c_entry_point(self):
        from OpenGL.GL.ARB.shader_objects import glShaderSourceARB

        assert self.is_c_entry_point(glShaderSourceARB)

    def test_a_customisation_that_drops_a_kept_argument_still_demotes(self):
        """The swallow is for arguments the C form has already dropped.

        A call that drops one the C form still takes builds a different
        function with a different arity, which the C cannot answer for -- so
        that one demotes, exactly as it does for a generated entry point.
        """
        from OpenGL import wrapper

        base = _dispatch.entry_points[('GL', 'glShaderSource')]
        derived = wrapper.wrapper(base).setPyConverter('string')
        assert not self.is_c_entry_point(derived)

    def test_demoting_it_keeps_the_arguments_a_caller_passes(self):
        """Assigning errcheck or argtypes moves one entry point to ctypes.

        What it moves to has to be the function the friendly module would have
        built, not the four-argument binding underneath it: the customisations
        the C performs were swallowed rather than applied, and demotion is
        where they have to be applied after all.

        Asked of what demotion installs rather than by demoting the live entry
        point, which is a decision for the life of the process and would leave
        every later test calling a different implementation than it meant to.
        """
        from OpenGL._dispatch import support

        demoted = support.demoted_callable(
            _dispatch.entry_points[('GL', 'glShaderSource')]
        )
        shader = glCreateShader(GL_VERTEX_SHADER)
        self.addCleanup(glDeleteShader, shader)
        demoted(shader, VERTEX_120)
        glCompileShader(shader)
        assert glGetShaderiv(shader, GL_COMPILE_STATUS) == GL_TRUE, glGetShaderInfoLog(
            shader
        )


class TestTransformFeedbackVaryings(GLTestCase):
    """``glTransformFeedbackVaryings(program, count, varyings, mode)``."""

    profile = 'core'
    gl_version = (3, 2)

    def setUp(self):
        super().setUp()
        self.program = glCreateProgram()
        self.addCleanup(glDeleteProgram, self.program)

    def records(self, count, varyings):
        glTransformFeedbackVaryings(self.program, count, varyings, GL_SEPARATE_ATTRIBS)
        self.check_error('glTransformFeedbackVaryings')

    def test_a_list_of_strings(self):
        self.records(1, ['carried'])

    def test_one_string(self):
        self.records(1, 'carried')

    def test_one_bytes(self):
        self.records(1, b'carried')

    def test_a_tuple_of_strings(self):
        self.records(1, ('carried',))

    def test_one_bytearray(self):
        self.records(1, bytearray(b'carried'))

    def test_a_list_of_bytearrays(self):
        self.records(1, [bytearray(b'carried')])

    def test_a_name_that_is_not_a_string_is_refused(self):
        with pytest.raises(REFUSED) as raised:
            self.records(2, ['carried', 42])
        assert 'int' in str(raised.value)

    def test_the_names_reach_the_driver(self):
        """A linked program reports the varying that was recorded."""
        vertex = glCreateShader(GL_VERTEX_SHADER)
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        self.addCleanup(glDeleteShader, vertex)
        self.addCleanup(glDeleteShader, fragment)
        glShaderSource(vertex, VERTEX_150)
        glShaderSource(fragment, FRAGMENT_150)
        for shader in (vertex, fragment):
            glCompileShader(shader)
            assert glGetShaderiv(shader, GL_COMPILE_STATUS) == GL_TRUE, (
                glGetShaderInfoLog(shader)
            )
            glAttachShader(self.program, shader)
        self.records(1, ['carried'])
        glLinkProgram(self.program)
        assert glGetProgramiv(self.program, GL_LINK_STATUS) == GL_TRUE, (
            glGetProgramInfoLog(self.program)
        )
        assert glGetProgramiv(self.program, GL_TRANSFORM_FEEDBACK_VARYINGS) == 1


class TestUniformIndices(GLTestCase):
    """``glGetUniformIndices(program, count, names, indices)``."""

    profile = 'core'
    gl_version = (3, 2)

    def test_a_list_of_names(self):
        program = self.compile_program(VERTEX_150, FRAGMENT_150)
        self.addCleanup(glDeleteProgram, program)
        indices = np.zeros(1, 'I')
        glGetUniformIndices(program, 1, ['tint'], indices)
        self.check_error('glGetUniformIndices')
        assert int(indices[0]) != GL_INVALID_INDEX

    def test_one_name(self):
        program = self.compile_program(VERTEX_150, FRAGMENT_150)
        self.addCleanup(glDeleteProgram, program)
        indices = np.zeros(1, 'I')
        glGetUniformIndices(program, 1, 'tint', indices)
        self.check_error('glGetUniformIndices')
        assert int(indices[0]) != GL_INVALID_INDEX


class TestShaderProgramv(GLTestCase):
    """``glCreateShaderProgramv(type, count, strings)`` compiles and links."""

    profile = 'core'
    gl_version = (4, 1)

    def links(self, strings, count=1):
        program = glCreateShaderProgramv(GL_FRAGMENT_SHADER, count, strings)
        self.addCleanup(glDeleteProgram, program)
        assert glGetProgramiv(program, GL_LINK_STATUS) == GL_TRUE, glGetProgramInfoLog(
            program
        )

    def test_a_list_of_strings(self):
        self.links([FRAGMENT_150.replace('in vec4 carried;', 'vec4 carried;')])

    def test_one_string(self):
        self.links(FRAGMENT_150.replace('in vec4 carried;', 'vec4 carried;'))


class TestASingleNameTakesTheSameForms(GLTestCase):
    """A ``GLchar *`` name accepts a ``str``, whatever else is configured.

    The same rule as the arrays above, for the far commoner single-name
    parameter: ``glBindAttribLocation``, ``glGetUniformLocation`` and their
    neighbours.  ``ERROR_ON_COPY`` refuses the copy of array data, and a name
    is not that -- it is encoded once at setup and read before the call
    returns.  The C dispatch layer has always encoded one; the ctypes path
    refusing it made a program that ran under one implementation fail under
    the other, and made the flag unusable for any code that looks up a uniform
    by name.
    """

    profile = 'core'
    gl_version = (3, 3)

    def test_a_str_name_is_accepted(self):
        program = glCreateProgram()
        try:
            glBindAttribLocation(program, 0, 'position')
            self.check_error('glBindAttribLocation with a str')
        finally:
            glDeleteProgram(program)

    def test_a_bytes_name_is_accepted(self):
        program = glCreateProgram()
        try:
            glBindAttribLocation(program, 0, b'position')
            self.check_error('glBindAttribLocation with bytes')
        finally:
            glDeleteProgram(program)


if __name__ == '__main__':
    unittest.main()
