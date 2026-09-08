"""Holds the import-time constants for various configuration flags"""
import OpenGL as _package

# A directory named `OpenGL` with no `__init__.py` in it, on sys.path, is
# imported as a namespace package -- and the finder that does that runs ahead
# of the one an editable install adds, so an empty directory wins over the
# real installation.  The submodules still load, because the editable
# install's finder answers for those by name, so what a caller sees is this
# import failing four frames inside some friendly module rather than
# `import OpenGL` failing.  Said here because this is the first module to read
# anything off the package, and because none of what follows is answerable:
# `__init__.py` never ran, so there are no flags to hold.
if getattr(_package, '__file__', None) is None:
    raise ImportError(
        'PyOpenGL was imported as a namespace package, so its OpenGL/'
        '__init__.py never ran and none of its configuration exists.  A '
        'directory named "OpenGL" with no __init__.py in it is on sys.path, '
        'and one found there is used ahead of an installed package.  It is '
        'at: %s.  Two things leave one: an install that replaced a wheel '
        'with an editable install of the same project and left the emptied '
        'directory behind, and a directory of that name in whichever '
        'directory the program was started from.'
        % (', '.join(_package.__path__) or 'no location this can name',)
    )

from OpenGL import (
    ERROR_CHECKING,
    ERROR_DEBUG_OUTPUT,
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
#: registry-generated C dispatch, or 'ctypes', the pure-Python one.  'c' is
#: the default from 4.0 on CPython, and takes effect where
#: PyOpenGL_accelerate is installed; where the extension is absent the layer
#: falls back to ctypes on its own, so this is safe to leave alone.
#: PYOPENGL_DISPATCH=ctypes selects the ctypes implementation, which remains
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

