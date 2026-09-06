"""OpenGL.GL.NV.conservative_raster_dilate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_CONSERVATIVE_RASTER_DILATE_GRANULARITY_NV: int
GL_CONSERVATIVE_RASTER_DILATE_NV: int
GL_CONSERVATIVE_RASTER_DILATE_RANGE_NV: int

def glConservativeRasterParameterfNV(pname: int, value: float) -> None: ...

def glInitConservativeRasterDilateNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
