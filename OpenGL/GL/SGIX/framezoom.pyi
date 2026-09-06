"""OpenGL.GL.SGIX.framezoom -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAMEZOOM_FACTOR_SGIX: int
GL_FRAMEZOOM_SGIX: int
GL_MAX_FRAMEZOOM_FACTOR_SGIX: int

def glFrameZoomSGIX(factor: int) -> None: ...

def glInitFramezoomSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
