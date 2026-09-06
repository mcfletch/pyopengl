"""OpenGL.GL.NV.vertex_array_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_MAX_VERTEX_ARRAY_RANGE_ELEMENT_NV: int
GL_VERTEX_ARRAY_RANGE_LENGTH_NV: int
GL_VERTEX_ARRAY_RANGE_NV: int
GL_VERTEX_ARRAY_RANGE_POINTER_NV: int
GL_VERTEX_ARRAY_RANGE_VALID_NV: int

def glFlushVertexArrayRangeNV() -> None: ...
def glVertexArrayRangeNV(length: int, pointer: AnyArray) -> None: ...

def glInitVertexArrayRangeNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
