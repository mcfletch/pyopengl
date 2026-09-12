#! /usr/bin/env python
"""Test for a buffer-protocol-based access mechanism

Will *only* work for Python 2.6+, and pretty much just works for strings
under 2.6 (in terms of the common object types).
"""
import ctypes
import sys, operator, logging, traceback
from OpenGL.arrays import _buffers
from OpenGL.raw.GL import _types

# from OpenGL.raw.GL.VERSION import GL_1_1
from OpenGL.arrays import formathandler
from OpenGL import _configflags
from OpenGL import acceleratesupport

_log = logging.getLogger(__name__)
from functools import reduce

MemoryviewHandler = BufferHandler = None
if sys.version_info[:2] > (2, 6):
    # Only Python 2.7+ has memoryview support, and the accelerate module
    # requires memoryviews to be able to pass around the buffer structures
    if acceleratesupport.ACCELERATE_AVAILABLE:
        try:
            from OpenGL_accelerate.buffers_formathandler import MemoryviewHandler
        except ImportError as err:
            traceback.print_exc()
            _log.warning(
                "Unable to load buffers_formathandler accelerator from OpenGL_accelerate"
            )
        else:
            BufferHandler = MemoryviewHandler
if not BufferHandler:

    class BufferHandler(formathandler.FormatHandler):
        """Buffer-protocol data-type handler for OpenGL"""

        isOutput = False
        ERROR_ON_COPY = _configflags.ERROR_ON_COPY
        if sys.version_info[0] >= 3:

            @classmethod
            def from_param(cls, value, typeCode=None):
                # Through `dataPointer`, which reads the address out of
                # whichever shape the value arrived in -- `asArray` now
                # answers with a memoryview, which has no `.buf`.
                return _types.GLvoidp(cls.dataPointer(value))

        else:

            @classmethod
            def from_param(cls, value, typeCode=None):
                return cls.dataPointer(value)

        def dataPointer(value):
            if not isinstance(value, _buffers.Py_buffer):
                value = _buffers.Py_buffer.from_object(value)
            return value.buf

        dataPointer = staticmethod(dataPointer)

        @classmethod
        def zeros(cls, dims, typeCode=None):
            """Currently don't allow strings as output types!"""
            raise NotImplementedError(
                "Generic buffer type does not have output capability"
            )
            return cls.asArray(
                bytearray(b'\000' * reduce(operator.mul, dims) * BYTE_SIZES[typeCode])
            )

        @classmethod
        def ones(cls, dims, typeCode=None):
            """Currently don't allow strings as output types!"""
            raise NotImplementedError("""Have not implemented ones for buffer type""")

        @staticmethod
        def _view(value):
            """`value` as a memoryview, whatever shape it arrived in.

            The accessors below are called with whatever a caller passed as
            well as with what `asArray` answered, so each has to read both.
            """
            if isinstance(value, memoryview):
                return value
            if isinstance(value, _buffers.Py_buffer):
                # A structure a previous release's `asArray` produced, and
                # what `dataPointer` still builds internally.
                return memoryview(
                    (ctypes.c_ubyte * value.len).from_address(value.buf))
            return memoryview(value)

        @classmethod
        def arrayToGLType(cls, value):
            """Given a value, guess OpenGL type of the corresponding pointer"""
            format = cls._view(value).format
            if format in ARRAY_TO_GL_TYPE_MAPPING:
                return ARRAY_TO_GL_TYPE_MAPPING[format]
            raise TypeError('Unknown format: %r' % (format,))

        @classmethod
        def arraySize(cls, value, typeCode=None):
            """Given a data-value, calculate ravelled size for the array"""
            view = cls._view(value)
            return view.nbytes // view.itemsize

        @classmethod
        def arrayByteCount(cls, value, typeCode=None):
            """Given a data-value, calculate number of bytes required to represent"""
            return cls._view(value).nbytes

        @classmethod
        def unitSize(cls, value, default=None):
            return cls._view(value).shape[-1]

        @classmethod
        def asArray(cls, value, typeCode=None):
            """Convert given value to an array value of given typeCode

            A ``memoryview``, which is what the compiled handler answers with
            too.  It used to be a ``Py_buffer`` -- and that is a
            ``ctypes.Structure``, which ctypes passes to a ``void *``
            parameter as *a pointer to the structure*.  So an entry point
            taking ``const void *data`` received the address of the wrapper
            and uploaded the wrapper's own bytes: right size, no GL error, and
            a pointer value in the buffer where the data should be.  A
            memoryview is passed by ctypes as the address of its data, which
            is what every one of these calls means.

            See https://github.com/mcfletch/pyopengl/issues/175
            """
            return cls._view(value)

        @classmethod
        def dimensions(cls, value, typeCode=None):
            """Determine dimensions of the passed array value (if possible)"""
            return cls._view(value).shape


ARRAY_TO_GL_TYPE_MAPPING = _buffers.ARRAY_TO_GL_TYPE_MAPPING
BYTE_SIZES = _buffers.BYTE_SIZES
