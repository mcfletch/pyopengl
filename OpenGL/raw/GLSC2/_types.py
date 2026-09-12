# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""The GL types the OpenGL SC 2.0 entry points are declared with.

OpenGL SC 2.0 is the safety-critical profile, and its types are ES 2.0's: the
profile is a subset of that API rather than a separate one, so the declarations
come from there rather than being restated.  What is its own is the error
check, which has to read *this* library's ``glGetError`` -- an implementation
may provide SC beside ES, and an error raised by one is not the other's.

`OpenGL.platform` loads no SC library on any platform here; one ships with a
conformant SC implementation rather than with a desktop driver.  The entry
points then report themselves unavailable when called, as every API a machine
lacks does, and importing the bindings still works.
"""
from OpenGL.raw.GLES2._types import *

from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker

# `_ErrorChecker` is None when PYOPENGL_ERROR_CHECKING is off -- there is
# no checker, which is the point of the flag -- so building one has to be
# conditional. Unguarded, turning error checking off made this module
# unimportable with `TypeError: 'NoneType' object is not callable`, from a
# line that names neither the flag nor the API.
# See OpenGL/raw/GL/_errors.py, which has always done this, and
# https://github.com/mcfletch/pyopengl/issues/166
_get_error = getattr( _p.GLSC2, 'glGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker( _p, _get_error )
else:
    _error_checker = None
