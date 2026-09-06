"""OpenGL.GL.ARB.draw_indirect -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_DRAW_INDIRECT_BUFFER: int
GL_DRAW_INDIRECT_BUFFER_BINDING: int

def glDrawArraysIndirect(mode: int, indirect: AnyArray) -> None: ...
def glDrawElementsIndirect(mode: int, type: int, indirect: AnyArray) -> None: ...

def glInitDrawIndirectARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
