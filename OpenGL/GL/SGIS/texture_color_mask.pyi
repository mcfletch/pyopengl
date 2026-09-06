"""OpenGL.GL.SGIS.texture_color_mask -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_TEXTURE_COLOR_WRITEMASK_SGIS: int

def glTextureColorMaskSGIS(red: bool, green: bool, blue: bool, alpha: bool) -> None: ...

def glInitTextureColorMaskSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
