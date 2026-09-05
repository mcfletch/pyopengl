# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
if _ErrorChecker:
    # GLX manages the display and the context, so its calls are made
    # before a GL context exists; see the EGL checker beside this one.
    _error_checker = _ErrorChecker( _p, None, needs_context = False )
else:
    _error_checker = None
