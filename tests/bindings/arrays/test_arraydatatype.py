#! /usr/bin/env python3
"""``ArrayDatatype``: the conversion, without a context to convert for.

Everything here is a question about the array handlers themselves -- what a
typed pointer answers, how many bytes an array occupies, which handler claims
an object exporting the buffer protocol -- so none of it opens a GL context.
The cases that pass the results of that conversion to an entry point are in
``gl/test_array_acceptance.py``, which does.
"""

import ctypes
import re
import struct
import sys
import unittest

import pytest

import OpenGL
from OpenGL import acceleratesupport
from OpenGL.arrays import arraydatatype
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL.raw.GL._types import GLfloat, GLint, GLuint

try:
    import numpy as np
except ImportError:
    np = None

#: Several of these are about the buffer protocol, which the C accelerator
#: implements and the pure-Python path does not.
needs_accelerate = pytest.mark.skipif(
    not acceleratesupport.ACCELERATE_AVAILABLE,
    reason='the buffer protocol support is the C accelerator\'s',
)

#: A PEP 3118 format string: an optional shape in parentheses, an optional
#: byte-order character, then the struct-module letter for the item type.
FORMAT = re.compile(r'^(?:\((?P<shape>[\d,]+)\))?(?P<order>[<>=!@])?(?P<letter>.+)$')

#: struct-module letters for a signed integer, of whatever width.
SIGNED_INTEGERS = frozenset('bhilqn')

#: And for an unsigned one.
UNSIGNED_INTEGERS = frozenset('BHILQN')


def format_letter(format):
    """The item-type letter of a Py_buffer format string.

    Which letter a platform uses for a given C type is the platform's
    business: a 4-byte signed int is ``i`` on x86-64 and ``l`` on i586 and
    armv7l, and the shape prefix comes and goes with the interpreter version.
    The byte-order character varies too -- ``<`` on a little-endian machine and
    ``>`` on s390x.

    So a case says what the value *is* and lets the machine spell it. Width is
    not lost by doing so: ``itemsize`` is asserted separately and is what pins
    it.

    https://github.com/mcfletch/pyopengl/issues/29
    https://github.com/mcfletch/pyopengl/issues/92
    """
    if isinstance(format, bytes):
        format = format.decode('ascii')
    match = FORMAT.match(format)
    assert match, 'not a buffer format string: %r' % (format,)
    return match.group('letter')


class TestReadingAFormatString:
    """``format_letter`` against the spellings the tracker has seen.

    Two tickets are one machine reporting a format string the case did not
    list, so the spellings from both are here -- and a machine that reports a
    fifth one now changes nothing.
    """

    @pytest.mark.parametrize(
        'format,letter',
        [
            (b'<i', 'i'),                # x86-64
            (b'(3)<i', 'i'),             # x86-64, through Py_buffer
            (b'<l', 'l'),                # i586 and armv7l, GH#29
            (b'(3)<l', 'l'),
            (b'>i', 'i'),                # s390x, GH#92
            (b'(3)>i', 'i'),
            (b'<q', 'q'),                # a 64-bit c_long
            (b'(3,3)<I', 'I'),           # a two-dimensional shape
            (b'B', 'B'),                 # no order character at all
            (b'I', 'I'),
        ],
    )
    def test_the_letter_is_read_whatever_surrounds_it(self, format, letter):
        assert format_letter(format) == letter

    def test_text_is_read_as_well_as_bytes(self):
        """CPython answers bytes; the reports quote str."""
        assert format_letter('(3)<l') == 'l'

    def test_every_signed_spelling_of_a_four_byte_int_is_signed(self):
        for format in (b'<i', b'(3)<i', b'<l', b'(3)<l', b'>i'):
            assert format_letter(format) in SIGNED_INTEGERS, format


class TestCoreDatatype(unittest.TestCase):
    def test_arrayPointer(self):
        dt = arraydatatype.GLuintArray
        d = dt.zeros((3,))
        dp = dt.typedPointer(d)
        assert dp[0] == 0
        assert dp[1] == 0
        assert dp[2] == 0
        dp[1] = 1
        assert dp[1] == 1
        assert d[1] == 1

    @needs_accelerate
    def test_buffer_api_basic(self):
        """What ``Py_buffer.from_object`` reports about an object's memory.

        A ``format`` given as a ``frozenset`` is a set of acceptable item-type
        letters rather than a whole format string; see ``format_letter`` above
        for why the spelling is the machine's to choose.
        """
        import array as silly_array

        structures = [
            (b'this and that', 13, 1, True, 1, UNSIGNED_INTEGERS, [13], [1]),
            (
                (GLint * 3)(1, 2, 3),
                12,
                4,
                False,
                1,
                SIGNED_INTEGERS,
                [3],
                None,
            ),
            (
                silly_array.array('I', [1, 2, 3]),
                12,
                4,
                False,
                1,
                UNSIGNED_INTEGERS,
                [3],
                [4],
            ),
            (memoryview(b'this'), 4, 1, True, 1, UNSIGNED_INTEGERS, [4], [1]),
        ]
        if np is not None:
            structures.extend(
                [
                    (
                        np.arange(0, 9, dtype='I').reshape((3, 3)),
                        36,
                        4,
                        False,
                        2,
                        UNSIGNED_INTEGERS,
                        [3, 3],
                        [12, 4],
                    ),
                    (
                        np.arange(0, 9, dtype='I').reshape((3, 3))[:, 1],
                        12,
                        4,
                        False,
                        1,
                        UNSIGNED_INTEGERS,
                        [3],
                        [12],
                    ),
                ]
            )

        from OpenGL.arrays import _buffers

        for (
            object,
            length,
            itemsize,
            readonly,
            ndim,
            format,
            shape,
            strides,
        ) in structures:
            buf = _buffers.Py_buffer.from_object(
                object, _buffers.PyBUF_STRIDES | _buffers.PyBUF_FORMAT
            )
            with buf:
                assert buf.len == length, (object, length, buf.len)
                assert buf.itemsize == itemsize, (object, itemsize, buf.itemsize)
                assert buf.readonly == readonly, (object, readonly, buf.readonly)
                assert buf.ndim == ndim, (object, ndim, buf.ndim)
                if isinstance(format, frozenset):
                    assert format_letter(buf.format) in format, (
                        object,
                        format,
                        buf.format,
                    )
                else:
                    assert buf.format == format, (object, format, buf.format)
                assert buf.shape[: buf.ndim] == shape, (
                    object,
                    shape,
                    buf.shape[: buf.ndim],
                )
                assert buf.dims == shape, (object, shape, buf.dims)
                assert buf.buf
                if strides is None:
                    assert not buf.strides
                else:
                    assert buf.strides[: buf.ndim] == strides, (
                        object,
                        strides,
                        buf.strides[: buf.ndim],
                    )
            assert buf.obj is None, buf.obj
            del buf


    def test_void_dp_for_void_dp_is_self(self):
        array = ctypes.c_voidp(12)
        translated = ArrayDatatype.voidDataPointer(array)
        assert translated.value == array.value, translated


    @pytest.mark.skipif(not np, reason="Numpy not available")
    def test_array_subclass(self):
        s = Subclassed([0, 1, 2, 3, 4])
        result = arraydatatype.ArrayDatatype.asArray(s)
        assert isinstance(result, Subclassed)

    @pytest.mark.skipif(not np, reason="Numpy not available")
    def test_byte_count_numpy(self):
        for a, expected in [
            (np.array([1, 2], dtype='e'), 4),
            (np.array([1, 2], dtype='f'), 8),
            (np.array([1, 2], dtype='d'), 16),
            (np.array([1, 2], dtype='B'), 2),
            (np.array([[1], [2]], dtype='B'), 2),
            (np.float32(), 4),
            (np.float64(), 8),
        ]:
            handler = arraydatatype.ArrayDatatype.getHandler(a)

            assert type(a) in handler.HANDLED_TYPES, type(a)
            calculated = arraydatatype.ArrayDatatype.arrayByteCount(a)
            assert calculated == expected, "Byte count for %s was %s, expected %s" % (
                a,
                calculated,
                expected,
            )

    def test_byte_count(self):
        for a, expected in [
            (ctypes.c_float(), 4),
            ((ctypes.c_float * 3 * 4)(), 4 * 3 * 4),
        ]:
            calculated = arraydatatype.ArrayDatatype.arrayByteCount(a)
            assert calculated == expected, "Byte count for %s was %s, expected %s" % (
                a,
                calculated,
                expected,
            )


if np:

    class Subclassed(np.ndarray):
        pass
