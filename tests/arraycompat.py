#! /usr/bin/env python3
"""Array constructors for the test suite, with a no-numpy fallback.

Many tests build their vertex / matrix / pixel / index data with a handful of
numpy constructors (``array``, ``zeros``, ``ones``, ``eye``, ``identity``) and
dtype objects (``uint8`` and friends).  numpy is optional for PyOpenGL, and the
tox ``num0`` environments install the suite deliberately *without* numpy to
exercise the pure-ctypes code paths -- so the tests must not hard-depend on it.

Tests therefore do::

    from arraycompat import np

and use ``np.array`` / ``np.zeros`` / ... as before.  When numpy is installed
``np`` *is* numpy.  When it is not, ``np`` is a tiny shim built on PyOpenGL's
own ctypes array handler (``OpenGL.arrays.ctypesarrays``); the arrays it returns
are plain ctypes arrays of the matching GL type, which PyOpenGL accepts
natively, including as output buffers for ``glGet*``.

The directory holding this module is named by ``pythonpath`` in
``pyproject.toml``, so every test directory (gl, gles, glu, ...) can import it.

Tests that need numpy proper (dtype objects, ``frombuffer``, ``np.testing``,
...) should instead ``pytest.importorskip('numpy')`` so they skip cleanly in the
no-numpy environments rather than relying on this shim.

:func:`copy_safe` is here for the other configuration axis: a case that passes
a plain Python list because a list is the readable way to write the data, and
that must build an array instead where the run has refused implicit copies.
"""
from __future__ import print_function

from OpenGL._configflags import ERROR_ON_COPY

try:
    import numpy as np  # noqa: F401  (re-exported)
except ImportError:
    from OpenGL.arrays._arrayconstants import GL_INTPTR, GL_SIZEIPTR
    from OpenGL.arrays.ctypesarrays import CtypesArrayHandler as _handler

    # numpy dtype names -> the typecodes PyOpenGL's ctypes handler understands.
    # Exposed as attributes so ``np.uint8`` & co. work as dtype arguments
    # (``np.zeros(shape, np.uint8)``) just like real numpy scalars.
    #
    # ``intp``/``uintp`` are numpy's pointer-sized integers, which is what GL
    # calls GLintptr and GLsizeiptr; those are the handler's keys for the type,
    # and there is no character code for it to use instead.
    _DTYPES = {
        'int8': 'b', 'uint8': 'B', 'byte': 'b', 'ubyte': 'B',
        'int16': 'h', 'uint16': 'H', 'short': 'h', 'ushort': 'H',
        'int32': 'i', 'uint32': 'I', 'intc': 'i', 'uintc': 'I',
        'int64': 'q', 'uint64': 'Q',
        'intp': GL_INTPTR, 'uintp': GL_SIZEIPTR,
        'float32': 'f', 'float64': 'd', 'single': 'f', 'double': 'd',
    }

    # numpy "kind+itemsize" dtype strings -> the handler's typecodes, so codes
    # like 'u4' (uint32) / 'u1' (uint8) work the same as in real numpy.
    _NUMPY_TYPECODES = {
        'u1': 'B', 'u2': 'H', 'u4': 'I', 'u8': 'Q',
        'i1': 'b', 'i2': 'h', 'i4': 'i', 'i8': 'q',
        'f4': 'f', 'f8': 'd',
        '?': 'B',  # numpy bool -> GLboolean (unsigned byte)
    }

    def _typecode(dtype):
        """Normalise a numpy-ish dtype to a handler typecode string.

        Accepts the shim's own typecode chars ('f', 'Q', ...), numpy
        "kind+itemsize" strings ('u8', 'f4', ...) and full numpy dtype *names*
        passed as plain strings ('uint64', 'float32', ...).  The last case is
        why we consult ``_DTYPES``: ``np.zeros(4, 'uint64')`` hands us the
        string 'uint64', which the handler does not understand on its own.
        """
        if dtype in _NUMPY_TYPECODES:
            return _NUMPY_TYPECODES[dtype]
        if dtype in _DTYPES:
            return _DTYPES[dtype]
        return dtype

    def _as_shape(shape):
        if isinstance(shape, (list, tuple)):
            return tuple(shape)
        return (shape,)

    def _shape_of(data):
        shape = []
        node = data
        while isinstance(node, (list, tuple)):
            shape.append(len(node))
            node = node[0] if node else None
        return tuple(shape)

    def _assign(arr, data):
        for i, item in enumerate(data):
            if isinstance(item, (list, tuple)):
                _assign(arr[i], item)
            else:
                arr[i] = item

    class _CtypesNumpyShim(object):
        """Minimal numpy-look-alike backed by PyOpenGL's ctypes arrays.

        Implements only the constructors the tests use.  ``zeros``/``ones``
        defer to the array handler; the rest build on its ``zeros``.  numpy
        dtype names (``uint8`` ...) are exposed as the matching typecode strings
        so they may be passed wherever a ``dtype`` is expected.
        """

        @staticmethod
        def zeros(shape, dtype='d'):
            return _handler.zeros(_as_shape(shape), _typecode(dtype))

        @staticmethod
        def ones(shape, dtype='d'):
            return _handler.ones(_as_shape(shape), _typecode(dtype))

        @staticmethod
        def array(data, dtype='d'):
            arr = _handler.zeros(_shape_of(data), _typecode(dtype))
            _assign(arr, data)
            return arr

        @staticmethod
        def eye(n, dtype='d'):
            arr = _handler.zeros((n, n), _typecode(dtype))
            for i in range(n):
                arr[i][i] = 1
            return arr

        @staticmethod
        def identity(n, dtype='d'):
            return _CtypesNumpyShim.eye(n, dtype)

    for _name, _code in _DTYPES.items():
        setattr(_CtypesNumpyShim, _name, _code)

    np = _CtypesNumpyShim()


def copy_safe(data, dtype):
    """``data`` as a plain list, or as an array where the run refuses copies.

    Passing a list to an entry point is how the list handler gets exercised,
    and PyOpenGL copying it into a buffer is the documented default -- so most
    cases should keep passing one, and this returns it unchanged.

    ``ERROR_ON_COPY`` is a caller saying it will not accept that copy, and
    under it the same list is a ``CopyError`` before the call is reached.  For
    a case where the list is *incidental* -- it needed some data and a list was
    the readable way to write it -- that is the run behaving correctly rather
    than the case failing, so it gets an array instead, which is what a program
    running under the flag has to do.

    A case that is *about* the flag, or about what the list handler does, does
    not use this: it passes a list on purpose and says what it expects.
    """
    if ERROR_ON_COPY:
        return np.array(data, dtype)
    return data


def one(generated):
    """The single name a ``glGen*(1)``-style call produced.

    ``SIZE_1_ARRAY_UNPACK`` decides whether a call that makes one object hands
    back the name or a one-element array holding it, so a caller that has not
    pinned the flag has to read both.  ``int()`` alone does not: numpy refuses
    to convert an array that is not zero-dimensional, so
    ``int(glGenTextures(1))`` -- which reads like the careful spelling -- works
    only while the flag is on.
    """
    try:
        return int(generated)
    except TypeError:
        return int(generated[0])


def object_names(*values):
    """GL object names as an entry point that takes an array of them wants.

    ``glDeleteTextures(2, object_names(*textures))``.  The values are whatever the
    generator handed back -- a numpy scalar, a ctypes value, an int -- and what
    goes down is an array of ``GLuint``, so the call reads the same whether or
    not the run has refused implicit copies.
    """
    return copy_safe([int(value) for value in values], 'I')


# --- backend-agnostic helpers -------------------------------------------------
# A few tests need operations that numpy arrays provide as methods/attributes.
# These helpers work whether ``np`` is real numpy or the ctypes shim, so the
# tests stay backend-agnostic instead of skipping without numpy.
import ctypes as _ctypes


def nbytes(a):
    """Number of bytes occupied by a numpy or ctypes array."""
    n = getattr(a, 'nbytes', None)
    if n is not None:
        return n
    return _ctypes.sizeof(a)


def _to_list(a):
    """Recursively convert a ctypes array to nested Python lists."""
    if isinstance(a, _ctypes.Array):
        return [_to_list(x) for x in a]
    return a


def astype(a, dtype):
    """Return a copy of array ``a`` cast to ``dtype`` (numpy or ctypes-backed)."""
    if hasattr(a, 'astype'):  # numpy
        return a.astype(dtype)
    return np.array(_to_list(a), dtype)


def ravel(a):
    """Flatten a numpy or (nested) ctypes array to a contiguous 1-D array.

    numpy arrays defer to ``a.ravel()``.  ctypes arrays -- which the no-numpy
    shim produces -- have no such method, so we walk the nested array to its
    scalar leaves and rebuild a flat ctypes array of the same element type.
    """
    if hasattr(a, 'ravel'):  # numpy
        return a.ravel()
    scalars = []

    def _walk(node):
        if isinstance(node, _ctypes.Array):
            for element in node:
                _walk(element)
        else:
            scalars.append(node)

    _walk(a)
    base = type(a)
    while isinstance(getattr(base, '_type_', None), type):
        base = base._type_
    return (base * len(scalars))(*scalars)


def shape(a):
    """Shape tuple of a numpy or (possibly nested) ctypes array."""
    s = getattr(a, 'shape', None)
    if s is not None:  # numpy
        return tuple(s)
    dims = []
    node = a
    while isinstance(node, _ctypes.Array):
        dims.append(len(node))
        node = node[0] if len(node) else None
    return tuple(dims)
