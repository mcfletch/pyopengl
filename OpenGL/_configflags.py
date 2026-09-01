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

#: Which implementation of the entry points to use: 'ctypes' (the reference
#: semantics, and the default) or 'c' (the registry-generated C dispatch).
#: See plans/C-DISPATCH.md and the documentation on PYOPENGL_DISPATCH.
DISPATCH = _os.environ.get('PYOPENGL_DISPATCH', 'ctypes').strip().lower()
