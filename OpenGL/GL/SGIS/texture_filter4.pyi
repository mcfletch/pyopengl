"""OpenGL.GL.SGIS.texture_filter4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_FILTER4_SGIS: int
GL_TEXTURE_FILTER4_SIZE_SGIS: int

def glGetTexFilterFuncSGIS(target: int, filter: int, weights: FloatArray) -> None: ...
def glTexFilterFuncSGIS(target: int, filter: int, n: int, weights: FloatArray) -> None: ...

def glInitTextureFilter4SGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
