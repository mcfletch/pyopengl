# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
_get_error = getattr( _p.GLES3, 'glGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker( _p, _get_error )
else:
    _error_checker = None

