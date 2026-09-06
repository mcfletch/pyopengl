"""OpenGL.GLES2.NV.instanced_arrays -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_VERTEX_ATTRIB_ARRAY_DIVISOR_NV: int

def glVertexAttribDivisorNV(index: int, divisor: int) -> None: ...

def glInitInstancedArraysNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
