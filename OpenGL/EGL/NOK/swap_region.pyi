"""OpenGL.EGL.NOK.swap_region -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

def eglSwapBuffersRegionNOK(dpy: Any, surface: Any, numRects: int, rects: IntArray) -> int: ...

def glInitSwapRegionNOK() -> bool: ...

def __getattr__(name: str) -> Any: ...
