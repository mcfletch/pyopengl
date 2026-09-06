"""OpenGL.GL.APPLE.texture_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult

from OpenGL.raw.GL._types import *

GL_STORAGE_CACHED_APPLE: int
GL_STORAGE_PRIVATE_APPLE: int
GL_STORAGE_SHARED_APPLE: int
GL_TEXTURE_RANGE_LENGTH_APPLE: int
GL_TEXTURE_RANGE_POINTER_APPLE: int
GL_TEXTURE_STORAGE_HINT_APPLE: int

def glGetTexParameterPointervAPPLE(target: int, pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glTextureRangeAPPLE(target: int, length: int, pointer: AnyArray) -> None: ...

def glInitTextureRangeAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
