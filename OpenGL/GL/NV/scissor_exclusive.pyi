"""OpenGL.GL.NV.scissor_exclusive -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GL._types import *

GL_SCISSOR_BOX_EXCLUSIVE_NV: int
GL_SCISSOR_TEST_EXCLUSIVE_NV: int

def glScissorExclusiveArrayvNV(first: int, count: int, v: IntArray) -> None: ...
def glScissorExclusiveNV(x: int, y: int, width: int, height: int) -> None: ...

def glInitScissorExclusiveNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
