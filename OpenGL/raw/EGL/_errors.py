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

if _ErrorChecker:
    _error_checker = _ErrorChecker( 
        _p.PLATFORM, 
        _p.PLATFORM.EGL.eglGetError, 
        0x3000, # EGL_SUCCESS,
        errorClass = EGLError,
    )
else:
    _ErrorChecker = None
