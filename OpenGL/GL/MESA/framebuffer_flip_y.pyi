"""OpenGL.GL.MESA.framebuffer_flip_y -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_FLIP_Y_MESA: int

def glFramebufferParameteriMESA(target: int, pname: int, param: int) -> None: ...
def glGetFramebufferParameterivMESA(target: int, pname: int, params: IntArray) -> None: ...

def glInitFramebufferFlipYMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
