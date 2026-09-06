"""OpenGL.GL.APPLE.object_purgeable -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_BUFFER_OBJECT_APPLE: int
GL_PURGEABLE_APPLE: int
GL_RELEASED_APPLE: int
GL_RETAINED_APPLE: int
GL_UNDEFINED_APPLE: int
GL_VOLATILE_APPLE: int

def glGetObjectParameterivAPPLE(objectType: int, name: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glObjectPurgeableAPPLE(objectType: int, name: int, option: int) -> int: ...
def glObjectUnpurgeableAPPLE(objectType: int, name: int, option: int) -> int: ...

def glInitObjectPurgeableAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
