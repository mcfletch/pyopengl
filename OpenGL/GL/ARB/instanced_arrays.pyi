"""OpenGL.GL.ARB.instanced_arrays -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_VERTEX_ATTRIB_ARRAY_DIVISOR_ARB: int

def glVertexAttribDivisorARB(index: int, divisor: int) -> None: ...

def glInitInstancedArraysARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
