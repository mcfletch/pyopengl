"""OpenGL.EGL.NV.post_sub_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_POST_SUB_BUFFER_SUPPORTED_NV: int

def eglPostSubBufferNV(dpy: Any, surface: Any, x: int, y: int, width: int, height: int) -> int: ...

def glInitPostSubBufferNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
