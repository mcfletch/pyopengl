"""OpenGL.GL.NV.conditional_render -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_QUERY_BY_REGION_NO_WAIT_NV: int
GL_QUERY_BY_REGION_WAIT_NV: int
GL_QUERY_NO_WAIT_NV: int
GL_QUERY_WAIT_NV: int

def glBeginConditionalRenderNV(id: int, mode: int) -> None: ...
def glEndConditionalRenderNV() -> None: ...

def glInitConditionalRenderNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
