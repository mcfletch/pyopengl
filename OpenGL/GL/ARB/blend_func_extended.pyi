"""OpenGL.GL.ARB.blend_func_extended -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray

from OpenGL.raw.GL._types import *

GL_MAX_DUAL_SOURCE_DRAW_BUFFERS: int
GL_ONE_MINUS_SRC1_ALPHA: int
GL_ONE_MINUS_SRC1_COLOR: int
GL_SRC1_ALPHA: int
GL_SRC1_COLOR: int

def glBindFragDataLocationIndexed(program: int, colorNumber: int, index: int, name: ByteArray) -> None: ...
def glGetFragDataIndex(program: int, name: ByteArray) -> int: ...

def glInitBlendFuncExtendedARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
