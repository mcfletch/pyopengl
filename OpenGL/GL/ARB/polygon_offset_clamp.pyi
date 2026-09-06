"""OpenGL.GL.ARB.polygon_offset_clamp -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_POLYGON_OFFSET_CLAMP: int

def glPolygonOffsetClamp(factor: float, units: float, clamp: float) -> None: ...

def glInitPolygonOffsetClampARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
