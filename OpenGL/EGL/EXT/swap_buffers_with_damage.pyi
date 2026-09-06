"""OpenGL.EGL.EXT.swap_buffers_with_damage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

def eglSwapBuffersWithDamageEXT(dpy: Any, surface: Any, rects: IntArray, n_rects: int) -> int: ...

def glInitSwapBuffersWithDamageEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
