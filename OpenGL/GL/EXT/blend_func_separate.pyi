"""OpenGL.GL.EXT.blend_func_separate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BLEND_DST_ALPHA_EXT: int
GL_BLEND_DST_RGB_EXT: int
GL_BLEND_SRC_ALPHA_EXT: int
GL_BLEND_SRC_RGB_EXT: int

def glBlendFuncSeparateEXT(sfactorRGB: int, dfactorRGB: int, sfactorAlpha: int, dfactorAlpha: int) -> None: ...

def glInitBlendFuncSeparateEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
