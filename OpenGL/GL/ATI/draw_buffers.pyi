"""OpenGL.GL.ATI.draw_buffers -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GL._types import *

GL_DRAW_BUFFER0_ATI: int
GL_DRAW_BUFFER10_ATI: int
GL_DRAW_BUFFER11_ATI: int
GL_DRAW_BUFFER12_ATI: int
GL_DRAW_BUFFER13_ATI: int
GL_DRAW_BUFFER14_ATI: int
GL_DRAW_BUFFER15_ATI: int
GL_DRAW_BUFFER1_ATI: int
GL_DRAW_BUFFER2_ATI: int
GL_DRAW_BUFFER3_ATI: int
GL_DRAW_BUFFER4_ATI: int
GL_DRAW_BUFFER5_ATI: int
GL_DRAW_BUFFER6_ATI: int
GL_DRAW_BUFFER7_ATI: int
GL_DRAW_BUFFER8_ATI: int
GL_DRAW_BUFFER9_ATI: int
GL_MAX_DRAW_BUFFERS_ATI: int

def glDrawBuffersATI(n: int, bufs: UIntArray) -> None: ...

def glInitDrawBuffersATI() -> bool: ...

def __getattr__(name: str) -> Any: ...
