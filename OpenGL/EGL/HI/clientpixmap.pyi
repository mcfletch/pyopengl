"""OpenGL.EGL.HI.clientpixmap -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.EGL._types import *

EGL_CLIENT_PIXMAP_POINTER_HI: int

def eglCreatePixmapSurfaceHI(dpy: Any, config: Any, pixmap: AnyArray) -> Any: ...

def glInitClientpixmapHI() -> bool: ...

def __getattr__(name: str) -> Any: ...
