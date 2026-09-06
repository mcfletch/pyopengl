"""OpenGL.EGL.ANGLE.query_surface_pointer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.EGL._types import *

def eglQuerySurfacePointerANGLE(dpy: Any, surface: Any, attribute: int, value: AnyArray) -> int: ...

def glInitQuerySurfacePointerANGLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
