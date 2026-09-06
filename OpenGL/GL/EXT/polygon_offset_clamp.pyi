"""OpenGL.GL.EXT.polygon_offset_clamp -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_POLYGON_OFFSET_CLAMP_EXT: int

def glPolygonOffsetClampEXT(factor: float, units: float, clamp: float) -> None: ...

def glInitPolygonOffsetClampEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
