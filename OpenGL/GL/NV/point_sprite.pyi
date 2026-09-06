"""OpenGL.GL.NV.point_sprite -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GL._types import *

GL_COORD_REPLACE_NV: int
GL_POINT_SPRITE_NV: int
GL_POINT_SPRITE_R_MODE_NV: int

def glPointParameteriNV(pname: int, param: int) -> None: ...
def glPointParameterivNV(pname: int, params: IntArray) -> None: ...

def glInitPointSpriteNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
