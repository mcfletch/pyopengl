"""OpenGL.GL.EXT.blend_minmax -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BLEND_EQUATION_EXT: int
GL_FUNC_ADD_EXT: int
GL_MAX_EXT: int
GL_MIN_EXT: int

def glBlendEquationEXT(mode: int) -> None: ...

def glInitBlendMinmaxEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
