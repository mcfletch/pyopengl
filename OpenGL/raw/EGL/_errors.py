from OpenGL.error import _ErrorChecker
from OpenGL import platform as _p

_error_checker = _ErrorChecker( 
    _p.PLATFORM, 
    _p.PLATFORM.EGL.eglGetError, 
    0x3000 # EGL_SUCCESS
)
