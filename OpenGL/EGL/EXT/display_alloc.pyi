"""OpenGL.EGL.EXT.display_alloc -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_ALLOC_NEW_DISPLAY_EXT: int

def eglDestroyDisplayEXT(dpy: Any) -> int: ...

def eglInitDisplayAllocEXT(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
