# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
if _ErrorChecker:
    _error_checker = _ErrorChecker( _p, None )
else:
    _error_checker = None
