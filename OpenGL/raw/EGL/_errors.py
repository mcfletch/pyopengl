# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
from OpenGL.error import _ErrorChecker, EGLError
from OpenGL import platform as _p

class EGLError( EGLError ):
    @property 
    def err(self):
        from OpenGL.EGL import debug
        return debug.eglErrorName(self.__dict__.get('err'))
    @err.setter 
    def err(self, value):
        self.__dict__['err'] = value

_get_error = getattr( _p.PLATFORM.EGL, 'eglGetError', None )
if _get_error and _ErrorChecker:
    _error_checker = _ErrorChecker(
        _p.PLATFORM,
        _get_error,
        0x3000, # EGL_SUCCESS,
        errorClass = EGLError,
        # EGL is how a program *gets* a GL context, so its calls are made
        # before there is one.  Gating on a current GL context would report no
        # EGL errors in the part of a program where every EGL call happens.
        needs_context = False,
    )
else:
    _error_checker = None

# Both implementations read this one statement of the policy: the ctypes
# bindings call the checker, and the compiled dispatch layer is handed the
# function it asks, the code it calls success and the class it raises.
from OpenGL import _dispatch as _d
_d.register_error_source('EGL', _error_checker)
