"""OpenGL.GL.ARB.provoking_vertex -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FIRST_VERTEX_CONVENTION: int
GL_LAST_VERTEX_CONVENTION: int
GL_PROVOKING_VERTEX: int
GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION: int

def glProvokingVertex(mode: int) -> None: ...

def glInitProvokingVertexARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
