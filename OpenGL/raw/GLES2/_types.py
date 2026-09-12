# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.raw.GLES1._types import *

from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
# `_ErrorChecker` is None when PYOPENGL_ERROR_CHECKING is off -- there is
# no checker, which is the point of the flag -- so building one has to be
# conditional. Unguarded, turning error checking off made this module
# unimportable with `TypeError: 'NoneType' object is not callable`, from a
# line that names neither the flag nor the API.
# See OpenGL/raw/GL/_errors.py, which has always done this, and
# https://github.com/mcfletch/pyopengl/issues/166
_get_error = getattr( _p.GLES2, 'glGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker( _p, _get_error )
else:
    _error_checker = None
