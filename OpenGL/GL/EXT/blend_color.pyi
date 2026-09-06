"""OpenGL.GL.EXT.blend_color -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BLEND_COLOR_EXT: int
GL_CONSTANT_ALPHA_EXT: int
GL_CONSTANT_COLOR_EXT: int
GL_ONE_MINUS_CONSTANT_ALPHA_EXT: int
GL_ONE_MINUS_CONSTANT_COLOR_EXT: int

def glBlendColorEXT(red: float, green: float, blue: float, alpha: float) -> None: ...

def glInitBlendColorEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
