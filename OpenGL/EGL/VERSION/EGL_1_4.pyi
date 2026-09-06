"""OpenGL.EGL.VERSION.EGL_1_4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_MULTISAMPLE_RESOLVE: int
EGL_MULTISAMPLE_RESOLVE_BOX: int
EGL_MULTISAMPLE_RESOLVE_BOX_BIT: int
EGL_MULTISAMPLE_RESOLVE_DEFAULT: int
EGL_OPENGL_API: int
EGL_OPENGL_BIT: int
EGL_SWAP_BEHAVIOR_PRESERVED_BIT: int

def eglGetCurrentContext() -> Any: ...

def glInitEgl14VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
