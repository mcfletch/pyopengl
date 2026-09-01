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

#: Which implementation of the entry points to use: 'c', the
#: registry-generated C dispatch, or 'ctypes', the one PyOpenGL has always
#: had.  'c' is the default from 4.0; where the extension was not built the
#: layer falls back to ctypes on its own, so this is safe to leave alone.
#: PYOPENGL_DISPATCH=ctypes selects the older implementation, which remains
#: supported and is not scheduled for removal.
DISPATCH = _os.environ.get('PYOPENGL_DISPATCH', 'c').strip().lower()
