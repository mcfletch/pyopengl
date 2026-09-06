"""OpenGL.GL.ARB.color_buffer_float -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_CLAMP_FRAGMENT_COLOR_ARB: int
GL_CLAMP_READ_COLOR_ARB: int
GL_CLAMP_VERTEX_COLOR_ARB: int
GL_FIXED_ONLY_ARB: int
GL_RGBA_FLOAT_MODE_ARB: int

def glClampColorARB(target: int, clamp: int) -> None: ...

def glInitColorBufferFloatARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
