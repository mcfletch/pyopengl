"""OpenGL.EGL.KHR.partial_update -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_BUFFER_AGE_KHR: int

def eglSetDamageRegionKHR(dpy: Any, surface: Any, rects: IntArray, n_rects: int) -> int: ...

def glInitPartialUpdateKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
