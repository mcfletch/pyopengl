#! /usr/bin/env python3
"""``ArrayDatatype``: the conversion, without a context to convert for.

Everything here is a question about the array handlers themselves -- what a
typed pointer answers, how many bytes an array occupies, which handler claims
an object exporting the buffer protocol -- so none of it opens a GL context.
The cases that pass the results of that conversion to an entry point are in
``gl/test_array_acceptance.py``, which does.
"""

import ctypes
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
        import array as silly_array

        structures = []
        if sys.version_info[:2] >= (3, 9):
            structures.append(
                (b'this and that', 13, 1, True, 1, b'B', [13], [1]),
            )

        if sys.version_info[:2] >= (2, 7):
            # GH#92 Big-endian hosts report different formats because yeah, obviously
            if sys.byteorder == 'little':  # x86 cases
                int_formats = [b'(3)<i', b'(3)<l', b'<i', b'<l']
            else:
                int_formats = [b'(3)>i', b'(3)>l', b'>i', b'>l']

            if sys.version_info[:2] not in [(3, 8), (3, 7)]:

                structures.append(
                    # on Python 3.4 we do *not* get the (3) prefix :(
                    (
                        (GLint * 3)(1, 2, 3),
                        12,
                        4,
                        False,
                        1,
                        int_formats,
                        [3],
                        None,
                    ),
                )

        if sys.version_info[:2] >= (3, 0) and sys.version_info[:2] not in [
            (3, 8),
            (3, 7),
        ]:
            # only supports buffer protocol in 3.x
            structures.extend(
                [
                    (
                        silly_array.array('I', [1, 2, 3]),
                        12,
                        4,
                        False,
                        1,
                        b'I',
                        [3],
                        [4],
                    ),
                ]
            )
        try:
            if sys.version_info[:2] not in [(3, 8), (3, 7)]:
                structures.append((memoryview(b'this'), 4, 1, True, 1, b'B', [4], [1]))
        except NameError:
            # Python 2.6 doesn't have memory view
            pass
        try:
            if array:
                structures.extend(
                    [
                        (
                            arange(0, 9, dtype='I').reshape((3, 3)),
                            36,
                            4,
                            False,
                            2,
                            b'I',
                            [3, 3],
                            [12, 4],
                        ),
                        (
                            arange(0, 9, dtype='I').reshape((3, 3))[:, 1],
                            12,
                            4,
                            False,
                            1,
                            b'I',
                            [3],
                            [12],
                        ),
                    ]
                )
        except NameError:
            # Don't have numpy installed...
            pass

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
                if isinstance(format, list):
                    assert buf.format in format, (object, format, buf.format)
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
