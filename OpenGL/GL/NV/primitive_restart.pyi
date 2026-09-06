"""OpenGL.GL.NV.primitive_restart -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_PRIMITIVE_RESTART_INDEX_NV: int
GL_PRIMITIVE_RESTART_NV: int

def glPrimitiveRestartIndexNV(index: int) -> None: ...
def glPrimitiveRestartNV() -> None: ...

def glInitPrimitiveRestartNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
