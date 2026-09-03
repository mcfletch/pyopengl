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

import pytest

numpy = pytest.importorskip('numpy')

from OpenGL.arrays import ArrayDatatype  # noqa: E402

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
