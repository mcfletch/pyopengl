# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.platform import PLATFORM as _p
from OpenGL.error import _ErrorChecker
_get_error = getattr( _p.GL, 'glGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker( _p, _get_error )
    # Desktop GL is the API GL_KHR_debug belongs to, so this checker is the one
    # that can stop paying for a glGetError per call.  The offer is made when
    # it first checks, because that is the first moment a context exists.
    from OpenGL import dispatch as _dispatch
    _dispatch.offer_on_first_check( _error_checker )
else:
    _error_checker = None

# Both implementations read this one statement of the policy: the ctypes
# bindings call the checker, and the compiled dispatch layer is handed the
# function it asks, the code it calls success and the class it raises.
from OpenGL import _dispatch as _d
_d.register_error_source('GL', _error_checker)
