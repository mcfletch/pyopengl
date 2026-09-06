"""OpenGL.GL.ARB.ES3_2_compatibility -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MULTISAMPLE_LINE_WIDTH_GRANULARITY_ARB: int
GL_MULTISAMPLE_LINE_WIDTH_RANGE_ARB: int
GL_PRIMITIVE_BOUNDING_BOX_ARB: int

def glPrimitiveBoundingBoxARB(minX: float, minY: float, minZ: float, minW: float, maxX: float, maxY: float, maxZ: float, maxW: float) -> None: ...

def glInitEs32CompatibilityARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
