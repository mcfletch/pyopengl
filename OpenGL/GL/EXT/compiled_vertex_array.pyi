"""OpenGL.GL.EXT.compiled_vertex_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ARRAY_ELEMENT_LOCK_COUNT_EXT: int
GL_ARRAY_ELEMENT_LOCK_FIRST_EXT: int

def glLockArraysEXT(first: int, count: int) -> None: ...
def glUnlockArraysEXT() -> None: ...

def glInitCompiledVertexArrayEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
