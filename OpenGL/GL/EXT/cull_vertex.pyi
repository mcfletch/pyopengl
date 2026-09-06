"""OpenGL.GL.EXT.cull_vertex -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import DoubleArray, DoubleArrayResult, FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_CULL_VERTEX_EXT: int
GL_CULL_VERTEX_EYE_POSITION_EXT: int
GL_CULL_VERTEX_OBJECT_POSITION_EXT: int

def glCullParameterdvEXT(pname: int, params: DoubleArray | None = None) -> DoubleArrayResult: ...
def glCullParameterfvEXT(pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...

def glInitCullVertexEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
