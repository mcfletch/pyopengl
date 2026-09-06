"""OpenGL.GL.NV.conservative_raster_pre_snap_triangles -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_CONSERVATIVE_RASTER_MODE_NV: int
GL_CONSERVATIVE_RASTER_MODE_POST_SNAP_NV: int
GL_CONSERVATIVE_RASTER_MODE_PRE_SNAP_TRIANGLES_NV: int

def glConservativeRasterParameteriNV(pname: int, param: int) -> None: ...

def glInitConservativeRasterPreSnapTrianglesNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
