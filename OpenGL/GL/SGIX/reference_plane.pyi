"""OpenGL.GL.SGIX.reference_plane -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import DoubleArray

from OpenGL.raw.GL._types import *

GL_REFERENCE_PLANE_EQUATION_SGIX: int
GL_REFERENCE_PLANE_SGIX: int

def glReferencePlaneSGIX(equation: DoubleArray) -> None: ...

def glInitReferencePlaneSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
