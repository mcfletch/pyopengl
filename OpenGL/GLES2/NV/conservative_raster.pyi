"""OpenGL.GLES2.NV.conservative_raster -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_CONSERVATIVE_RASTERIZATION_NV: int
GL_MAX_SUBPIXEL_PRECISION_BIAS_BITS_NV: int
GL_SUBPIXEL_PRECISION_BIAS_X_BITS_NV: int
GL_SUBPIXEL_PRECISION_BIAS_Y_BITS_NV: int

def glSubpixelPrecisionBiasNV(xbits: int, ybits: int) -> None: ...

def glInitConservativeRasterNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
