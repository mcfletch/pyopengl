"""OpenGL.GLES2.OES.primitive_bounding_box -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_PRIMITIVE_BOUNDING_BOX_OES: int

def glPrimitiveBoundingBoxOES(minX: float, minY: float, minZ: float, minW: float, maxX: float, maxY: float, maxZ: float, maxW: float) -> None: ...

def glInitPrimitiveBoundingBoxOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
