# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
_get_error = getattr( _p.GL, 'glGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker( _p, _get_error )
else:
    _error_checker = None

# Both implementations read this one statement of the policy: the ctypes
# bindings call the checker, and the compiled dispatch layer is handed the
# function it asks, the code it calls success and the class it raises.
from OpenGL import _dispatch as _d
_d.register_error_source('GL', _error_checker)
