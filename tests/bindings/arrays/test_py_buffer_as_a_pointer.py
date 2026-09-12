#! /usr/bin/env python3
"""A ``Py_buffer`` handed to a pointer argument passes the data, not itself.

``Py_buffer`` is the ctypes mirror of CPython's buffer structure, and it is
what the no-accelerate array machinery turns a ``memoryview``, a ``bytearray``
or anything else supporting the buffer protocol into. Its first field holds
the address of the data.

It is also a ``ctypes.Structure``, and ctypes passes one of those to a
``void *`` parameter as *a pointer to the structure*. So an entry point
declared ``const void *data`` -- ``glBufferData``, ``glBufferSubData``,
``glTexImage2D`` -- received the address of the wrapper rather than of the
data, and uploaded the wrapper's own bytes. The size was right, the call
succeeded, `glGetError` said nothing, and the buffer held a pointer value
where the mesh should be.

Only without the compiled accelerators: with them, ``asArray`` answers with
the ``memoryview`` itself and ctypes reads that correctly. So this is a defect
of the pure-Python configuration -- which is what runs on PyPy, on any
platform with no wheel, and wherever ``PYOPENGL_USE_ACCELERATE=0``.

https://github.com/mcfletch/pyopengl/issues/175
"""

import ctypes

import pytest

from OpenGL.arrays import _buffers

#: Distinct per four-byte group, so a wrong address shows up as wrong content
#: rather than as zeroes that might have been right.
PAYLOAD = b''.join(bytes([n]) * 4 for n in range(16))


@pytest.fixture
def buffer():
    """A Py_buffer over PAYLOAD, as the array machinery builds one."""
    view = memoryview(PAYLOAD)
    made = _buffers.Py_buffer.from_object(view)
    yield made
    del made


def test_it_holds_the_address_of_the_data(buffer):
    """The premise: the structure knows where the data is."""
    assert buffer.buf
    assert ctypes.string_at(buffer.buf, 8) == PAYLOAD[:8]


def test_it_declares_how_ctypes_should_pass_it(buffer):
    """Without this ctypes falls back to "a pointer to the structure"."""
    assert hasattr(buffer, '_as_parameter_'), (
        'Py_buffer does not say how to pass it, so ctypes passes the address '
        'of the structure and the caller uploads the wrapper')


def test_what_it_passes_is_the_data(buffer):
    passed = buffer._as_parameter_
    address = getattr(passed, 'value', passed)
    assert address == buffer.buf, (
        'passed %r where the data is at %r' % (address, buffer.buf))


def test_a_void_pointer_argument_receives_the_data(buffer):
    """Through ctypes itself, which is the thing that was getting it wrong."""
    function = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p)
    # memmove's first argument is a void*; use it to read back what ctypes
    # decided to pass, without needing a GL context.
    received = ctypes.c_void_p()

    def record(pointer):
        received.value = pointer
        return pointer

    recorder = function(record)
    recorder(buffer)
    assert received.value == buffer.buf, (
        'ctypes passed %r; the data is at %r'
        % (received.value, buffer.buf))
