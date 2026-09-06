"""OpenGL.GL.ARB.clip_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_CLIP_DEPTH_MODE: int
GL_CLIP_ORIGIN: int
GL_LOWER_LEFT: int
GL_NEGATIVE_ONE_TO_ONE: int
GL_UPPER_LEFT: int
GL_ZERO_TO_ONE: int

def glClipControl(origin: int, depth: int) -> None: ...

def glInitClipControlARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
