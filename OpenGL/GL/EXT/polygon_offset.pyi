"""OpenGL.GL.EXT.polygon_offset -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_POLYGON_OFFSET_BIAS_EXT: int
GL_POLYGON_OFFSET_EXT: int
GL_POLYGON_OFFSET_FACTOR_EXT: int

def glPolygonOffsetEXT(factor: float, bias: float) -> None: ...

def glInitPolygonOffsetEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
