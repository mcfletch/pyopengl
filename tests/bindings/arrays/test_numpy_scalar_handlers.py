"""Every numpy scalar type PyOpenGL can hand back has an array handler.

numpy names its scalar types twice: by width (``uint32``) and after the C type
of that width (``uintc``).  Whether the two names are the same object depends
on the platform's C model, so registering only the width names covers the C
names on LP64 (Linux, macOS) and not on LLP64 (Windows), where ``uintc`` and
``uint32`` are separate types.

It shows up where a value PyOpenGL returned is passed back in:
``buffer = glGenBuffers(1)`` unwraps to a scalar, and handing that to
``glGenVertexArrays(1, buffer)`` is a lookup for the scalar's own type.
"""

import ctypes
import warnings

import pytest

numpy = pytest.importorskip('numpy')

from OpenGL.arrays import ArrayDatatype  # noqa: E402


def _ctypes_refuses_a_float():
    """Whether this interpreter refuses a float where an integer is wanted.

    ``GLint`` is ``ctypes.c_int``, so the refusal is ctypes' rather than this
    package's.  CPython converted through ``__int__`` until 3.10 and PyPy
    still does, and making it refuse there would mean a ``from_param`` of our
    own -- which is the retry ``ALLOW_NUMPY_SCALARS`` used to install.  Asked
    of the interpreter rather than worked out from its version number,
    because it is the interpreter's answer that decides what is testable.
    """
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:
            ctypes.c_int.from_param(numpy.float32(1.5))
        except TypeError:
            return True
    return False


CTYPES_REFUSES_A_FLOAT = _ctypes_refuses_a_float()

#: The C-named aliases, which are the ones a ctypes-derived array yields.
C_NAMED = (
    'byte',
    'ubyte',
    'short',
    'ushort',
    'intc',
    'uintc',
    'int_',
    'uint',
    'longlong',
    'ulonglong',
    'single',
    'double',
)

#: The width-named aliases, for the same question from the other direction.
WIDTH_NAMED = (
    'int8',
    'uint8',
    'int16',
    'uint16',
    'int32',
    'uint32',
    'int64',
    'uint64',
    'float32',
    'float64',
)


@pytest.mark.parametrize('name', C_NAMED + WIDTH_NAMED)
def test_the_scalar_type_has_a_handler(name):
    scalar_type = getattr(numpy, name, None)
    if scalar_type is None:
        pytest.skip('this numpy has no %s' % (name,))
    ArrayDatatype.getHandler(scalar_type(1))


class TestPassingAScalarAsAnArgument:
    """A numpy scalar where a plain ``GLint`` / ``GLfloat`` is wanted.

    ctypes converts a numpy *integer* scalar itself, through ``__index__``, so
    ``glBindTexture(GL_TEXTURE_2D, glGenTextures(2)[0])`` works with nothing
    doing anything on its behalf.  A numpy *float* where an integer is wanted
    is a caller's mistake and is refused.

    ``ALLOW_NUMPY_SCALARS`` used to switch on a retry through ``long()`` that
    accepted the float and truncated it.  It has no effect from 4.0, and these
    run in children because the flag is read while the types are being built.
    """

    #: Reported as three words on stdout: whether the flag was set, whether an
    #: integer scalar converted, whether a float scalar converted.
    REPORT = r'''
import json
import numpy

from OpenGL import _configflags
from OpenGL.raw.GL import _types


def converts(value):
    try:
        _types.GLint.from_param(value)
    except TypeError:
        return False
    return True


print(json.dumps({
    'flag': bool(_configflags.ALLOW_NUMPY_SCALARS),
    'integer': converts(numpy.uint32(7)),
    'float': converts(numpy.float32(1.5)),
}))
'''

    def report(self, **environment):
        import json
        import os
        import subprocess
        import sys

        from childenv import run_in_child

        completed = run_in_child(self.REPORT, **environment)
        assert completed.returncode == 0, completed.stderr[-2000:]
        return json.loads(completed.stdout)

    def test_an_integer_scalar_is_accepted(self):
        assert self.report()['integer']

    @pytest.mark.skipif(
        not CTYPES_REFUSES_A_FLOAT,
        reason="this interpreter's ctypes converts through __int__, so the "
               "refusal is not this package's to make",
    )
    def test_a_float_scalar_is_refused_where_an_integer_is_wanted(self):
        assert not self.report()['float']

    def test_asking_for_the_old_behaviour_changes_nothing(self):
        """The flag is readable, and reading it is all it does now.

        Against this interpreter's own answer rather than against a fixed
        one, so that what is asserted is that the flag installs nothing --
        which is the claim -- on the interpreters that refuse a float and on
        those that do not.
        """
        asked = self.report(PYOPENGL_ALLOW_NUMPY_SCALARS='1')
        plain = self.report()
        assert asked['flag'], 'the flag no longer reads back at all'
        assert asked['integer']
        assert asked['float'] == plain['float'], (
            'ALLOW_NUMPY_SCALARS still changes what a GLint accepts'
        )
        if CTYPES_REFUSES_A_FLOAT:
            assert not asked['float'], (
                'ALLOW_NUMPY_SCALARS still installs the long() retry, which '
                'accepts a numpy float where an integer is wanted'
            )
