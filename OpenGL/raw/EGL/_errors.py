from OpenGL.error import _ErrorChecker
from OpenGL.platform import PLATFORM as _p

_error_checker = _ErrorChecker( 
    _p, 
    _p.EGL.eglGetError, 
    0x3000 # EGL_SUCCESS
)
