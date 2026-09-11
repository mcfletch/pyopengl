"""The emitter for the three hand-maintained libraries -- GLU, GLUT, GLE.

They are not in the Khronos registry, so nothing derives their declarations
from a command record; the stubs are read out of the modules themselves, and
the wrapper-built forms are read out of the wrappers.

What is checked here is the reading, not the stubs -- those are held to the
runtime forms in ``tests/bindings/generated/test_handwritten_api_stubs.py``.
The two failures that matter to a generator are the ones a stub cannot show:
a declaration read as the wrong kind of thing, and a whole class of entry
point quietly missing because something on the way in did not import.
"""

import ast

import pytest

from cdispatch import emit_handwritten


def assignment(source):
    """The single assignment statement in ``source``, for the readers below."""
    return ast.parse(source).body[0]


class TestReadingAFactoryCall:
    """Which factory a ``name = factory(...)`` line calls decides what the
    declaration says, and the factories are a closed set of three."""

    def declaration(self, source, api='GLUT'):
        lines = {}
        emit_handwritten._factory_declaration(assignment(source), lines)
        return lines

    def test_a_constant_is_an_int(self):
        assert self.declaration('GLUT_RGB = Constant(0)') == {
            'GLUT_RGB': 'GLUT_RGB: int'}

    def test_a_callback_registration_takes_the_function(self):
        found = self.declaration('glutDisplayFunc = GLUTCallback(0, (), ())')
        assert 'Callable[..., Any] | None' in found['glutDisplayFunc']

    def test_the_timer_form_takes_the_delay_and_the_value_too(self):
        found = self.declaration(
            'glutTimerFunc = GLUTTimerCallback(0, (), ())')
        assert 'milliseconds: int' in found['glutTimerFunc']
        assert 'value: int' in found['glutTimerFunc']

    def test_a_factory_is_matched_through_the_module_it_is_reached_by(self):
        """``platform.createBaseFunction`` is how every one of them is
        written."""
        found = self.declaration(
            "glutSwapBuffers = platform.createBaseFunction('glutSwapBuffers',"
            " dll=platform.PLATFORM.GLUT, resultType=None, argTypes=[],"
            " doc='', argNames=())")
        assert found['glutSwapBuffers'].startswith('def glutSwapBuffers(')

    def test_a_name_merely_ending_in_a_factory_name_is_not_one(self):
        """The factory is matched exactly rather than by suffix: a call to
        something called ``MyConstant`` is not a call to ``Constant``, and
        declaring it as an int would put a wrong type in the shipped stub."""
        assert self.declaration('gluSomething = enums.MyConstant(0)') == {}

    def test_nor_is_one_merely_containing_it(self):
        assert self.declaration('gluSomething = ConstantFolder(0)') == {}


class TestTheWrapperBuiltForms:
    """These take fewer arguments than the C form, and only the wrapper knows
    which ones went -- so they are read by importing the API and asking."""

    def test_an_api_that_will_not_import_is_reported(self):
        """Rather than answering "no wrapper-built entry points": that would
        write a stub carrying the C form of every call a program makes with
        fewer arguments, and report success doing it -- which is the defect
        (``glDeleteTextures``) this whole stub surface exists to prevent."""
        with pytest.raises(RuntimeError) as caught:
            emit_handwritten._wrapper_built('/nowhere', 'NotAnAPI')
        assert 'NotAnAPI' in str(caught.value)

    def test_a_real_api_answers_the_forms_the_wrapper_built(self):
        found = emit_handwritten._wrapper_built(None, 'GLU')
        assert found, 'GLU builds wrappers; none were read'
        assert all(line.startswith('def ') for line in found.values())
