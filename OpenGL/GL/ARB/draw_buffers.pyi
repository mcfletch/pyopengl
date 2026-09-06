"""OpenGL.GL.ARB.draw_buffers -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GL._types import *

GL_DRAW_BUFFER0_ARB: int
GL_DRAW_BUFFER10_ARB: int
GL_DRAW_BUFFER11_ARB: int
GL_DRAW_BUFFER12_ARB: int
GL_DRAW_BUFFER13_ARB: int
GL_DRAW_BUFFER14_ARB: int
GL_DRAW_BUFFER15_ARB: int
GL_DRAW_BUFFER1_ARB: int
GL_DRAW_BUFFER2_ARB: int
GL_DRAW_BUFFER3_ARB: int
GL_DRAW_BUFFER4_ARB: int
GL_DRAW_BUFFER5_ARB: int
GL_DRAW_BUFFER6_ARB: int
GL_DRAW_BUFFER7_ARB: int
GL_DRAW_BUFFER8_ARB: int
GL_DRAW_BUFFER9_ARB: int
GL_MAX_DRAW_BUFFERS_ARB: int

def glDrawBuffersARB(n: int, bufs: UIntArray) -> None: ...

def glInitDrawBuffersARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
