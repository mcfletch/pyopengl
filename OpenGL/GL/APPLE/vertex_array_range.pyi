"""OpenGL.GL.APPLE.vertex_array_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult

from OpenGL.raw.GL._types import *

GL_STORAGE_CACHED_APPLE: int
GL_STORAGE_CLIENT_APPLE: int
GL_STORAGE_SHARED_APPLE: int
GL_VERTEX_ARRAY_RANGE_APPLE: int
GL_VERTEX_ARRAY_RANGE_LENGTH_APPLE: int
GL_VERTEX_ARRAY_RANGE_POINTER_APPLE: int
GL_VERTEX_ARRAY_STORAGE_HINT_APPLE: int

def glFlushVertexArrayRangeAPPLE(length: int, pointer: AnyArray | None = None) -> AnyArrayResult: ...
def glVertexArrayParameteriAPPLE(pname: int, param: int) -> None: ...
def glVertexArrayRangeAPPLE(length: int, pointer: AnyArray | None = None) -> AnyArrayResult: ...

def glInitVertexArrayRangeAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
