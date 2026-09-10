#! /usr/bin/env python3
"""Allocating the array an entry point fills, whichever handler is installed.

``glGenTextures(3)`` and friends produce their own result: the wrapper asks the
output handler for an array of that size and hands the pointer to the driver.
Which handler answers depends on what is installed -- numpy where it is there,
ctypes where it is not -- and the two have to accept the same call, or a
program that runs on one installation raises ``TypeError`` on the other before
it draws anything.

The shapes are what ``numpy.zeros`` accepts: a single length, or a sequence of
them. An entry point producing `n` values asks for `n`.
"""

import pytest

from OpenGL.arrays.ctypesarrays import CtypesArrayHandler
from OpenGL.arrays.ctypesparameters import CtypesParameterHandler
from OpenGL.raw.GL._types import GL_FLOAT, GL_UNSIGNED_INT

#: Every output handler PyOpenGL can pick, by the name it is known as.
HANDLERS = {'ctypes array': CtypesArrayHandler}
try:
    import numpy  # noqa: F401
except ImportError:                             # pragma: no cover - no numpy
    pass
else:
    from OpenGL.arrays.numpymodule import NumpyHandler

    HANDLERS['numpy'] = NumpyHandler


@pytest.fixture(params=sorted(HANDLERS))
def handler(request):
    """An instance, which is what the registry hands the wrappers."""
    return HANDLERS[request.param]()


class TestTheShapesAHandlerTakes:
    def test_a_single_length(self, handler):
        """What an entry point producing `n` values asks for."""
        assert len(handler.zeros(3, GL_UNSIGNED_INT)) == 3

    def test_a_length_in_a_sequence(self, handler):
        assert len(handler.zeros((3,), GL_UNSIGNED_INT)) == 3

    def test_two_dimensions(self, handler):
        made = handler.zeros((2, 3), GL_FLOAT)
        assert len(made) == 2
        assert len(made[0]) == 3

    def test_it_starts_at_zero(self, handler):
        assert [int(value) for value in handler.zeros(4, GL_UNSIGNED_INT)] == [0] * 4


class TestTheParameterHandlerTakesTheSameShapes:
    """``ctypesparameters`` is the handler for a ctypes scalar passed by
    reference, and allocates output the same way."""

    def handler(self):
        return CtypesParameterHandler()

    def test_a_single_length(self):
        assert len(self.handler().zeros(3, GL_UNSIGNED_INT)) == 3

    def test_a_length_in_a_sequence(self):
        assert len(self.handler().zeros((3,), GL_UNSIGNED_INT)) == 3


class TestTheDatatypeAsksForOne:
    """Through ``ArrayDatatype``, which is what the wrappers call and what the
    compiled dispatch layer calls: the accelerated one forwards the size it was
    given rather than reshaping it."""

    def test_a_single_length_reaches_the_handler(self):
        from OpenGL.arrays.arraydatatype import GLuintArray

        assert len(GLuintArray.zeros(2)) == 2

    def test_a_length_in_a_sequence_does_too(self):
        from OpenGL.arrays.arraydatatype import GLuintArray

        assert len(GLuintArray.zeros((2,))) == 2
