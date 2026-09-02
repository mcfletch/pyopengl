"""Holds the import-time constants for various configuration flags"""
from OpenGL import (
    ERROR_CHECKING,
    ERROR_LOGGING,
    ERROR_ON_COPY,
    ARRAY_SIZE_CHECKING,
    STORE_POINTERS,
    WARN_ON_FORMAT_UNAVAILABLE,
    FORWARD_COMPATIBLE_ONLY,
    SIZE_1_ARRAY_UNPACK,
    USE_ACCELERATE,
    CONTEXT_CHECKING,

    FULL_LOGGING,
    ALLOW_NUMPY_SCALARS,
    UNSIGNED_BYTE_IMAGES_AS_STRING,
    MODULE_ANNOTATIONS,
    TYPE_ANNOTATIONS,
)

import os as _os
import sys as _sys

#: Which implementation of the entry points to use: 'c', the
#: registry-generated C dispatch, or 'ctypes', the one PyOpenGL has always
#: had.  'c' is the default from 4.0; where the extension was not built the
#: layer falls back to ctypes on its own, so this is safe to leave alone.
#: PYOPENGL_DISPATCH=ctypes selects the older implementation, which remains
#: supported and is not scheduled for removal.
#: Off CPython the C layer is not built (see accelerate/setup.py) and would be
#: slower than ctypes if it were, so the default follows the interpreter.
_DEFAULT_DISPATCH = 'c' if _sys.implementation.name == 'cpython' else 'ctypes'
DISPATCH = _os.environ.get('PYOPENGL_DISPATCH', _DEFAULT_DISPATCH).strip().lower()

#: Call tracing is a ctypes-layer feature: the wrapper chain is where the log
#: line is written, and the C calls the driver directly.  Somebody who turns
#: tracing on to find out what their program is calling must not be handed
#: silence and conclude the calls are not happening -- so asking for the trace
#: selects the implementation that can produce it.
if FULL_LOGGING and DISPATCH == 'c':
    DISPATCH = 'ctypes'

#: Build the generated OpenGL.raw modules from the C dispatch layer's tables
#: rather than importing their files.  Off by default: the files are still
#: shipped, and with the friendly modules importing the raw ones eagerly there
#: is nothing to be saved by shadowing them.  See OpenGL/_dispatch/finder.py.
VIRTUAL_MODULES = _os.environ.get('PYOPENGL_VIRTUAL_MODULES', '0').strip().lower() in (
    '1',
    'true',
    'yes',
)
