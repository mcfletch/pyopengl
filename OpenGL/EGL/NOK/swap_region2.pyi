"""OpenGL.EGL.NOK.swap_region2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

def eglSwapBuffersRegion2NOK(dpy: Any, surface: Any, numRects: int, rects: IntArray) -> int: ...

def glInitSwapRegion2NOK() -> bool: ...

def __getattr__(name: str) -> Any: ...
