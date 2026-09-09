"""OpenGL.GL.SGIS.texture_color_mask -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_TEXTURE_COLOR_WRITEMASK_SGIS: int

def glTextureColorMaskSGIS(red: int, green: int, blue: int, alpha: int) -> None: ...

def glInitTextureColorMaskSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
