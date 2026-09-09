#! /usr/bin/env python3
"""Asking whether an entry point is there, in a way a checker can read.

An entry point answers ``bool()`` with whether the driver serves it, so
``if glPointParameterf:`` is how a program guards an optional call.  A stub
declares the entry point as a function, and a function object is always true --
so a type checker reports the guard as a mistake (``truthy-function``) on code
that is right.  Silencing that per call site would take the check away from the
place it does catch a missing ``()``.

:func:`OpenGL.extensions.available` is the same question asked as a call.
"""

import pytest

from OpenGL import extensions


@pytest.fixture
def present():
    """An entry point every GL has."""
    from OpenGL.raw.GL.VERSION.GL_1_1 import glBindTexture
    return glBindTexture


@pytest.fixture
def absent():
    """One this driver does not serve.

    ``GL_NV_path_rendering`` is a vendor extension, so a non-NVIDIA driver has
    none of it; where a driver does serve it, the test says so and skips rather
    than asserting the opposite of what the machine reports.
    """
    from OpenGL.raw.GL.NV.path_rendering import glWeightPathsNV
    if glWeightPathsNV:
        pytest.skip('this driver serves GL_NV_path_rendering')
    return glWeightPathsNV


def test_an_entry_point_the_driver_serves_is_available(present):
    assert extensions.available(present) is True


def test_one_it_does_not_serve_is_not(absent):
    assert extensions.available(absent) is False


def test_it_answers_the_same_question_the_truthiness_does(present, absent):
    for entry_point in (present, absent):
        assert extensions.available(entry_point) == bool(entry_point)


def test_it_answers_for_a_wrapped_entry_point():
    """A friendly module's wrapper delegates the question to what it wraps."""
    from OpenGL.GL import glBindTexture
    assert extensions.available(glBindTexture) is True


def test_a_missing_name_is_not_available():
    """``getattr(module, name, None)`` is how a caller reaches an optional one."""
    assert extensions.available(None) is False
