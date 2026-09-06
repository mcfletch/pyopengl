"""OpenGL.GL.ARB.clear_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_CLEAR_TEXTURE: int

def glClearTexImage(texture: int, level: int, format: int, type: int, data: AnyArray) -> None: ...
def glClearTexSubImage(texture: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, type: int, data: AnyArray) -> None: ...

def glInitClearTextureARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
