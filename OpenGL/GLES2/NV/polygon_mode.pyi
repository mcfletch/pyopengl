"""OpenGL.GLES2.NV.polygon_mode -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FILL_NV: int
GL_LINE_NV: int
GL_POINT_NV: int
GL_POLYGON_MODE_NV: int
GL_POLYGON_OFFSET_LINE_NV: int
GL_POLYGON_OFFSET_POINT_NV: int

def glPolygonModeNV(face: int, mode: int) -> None: ...

def glInitPolygonModeNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
