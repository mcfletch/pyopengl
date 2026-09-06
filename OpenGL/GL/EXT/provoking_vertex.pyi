"""OpenGL.GL.EXT.provoking_vertex -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FIRST_VERTEX_CONVENTION_EXT: int
GL_LAST_VERTEX_CONVENTION_EXT: int
GL_PROVOKING_VERTEX_EXT: int
GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION_EXT: int

def glProvokingVertexEXT(mode: int) -> None: ...

def glInitProvokingVertexEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
