"""OpenGL.GL.SGIX.sprite -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, IntArray

from OpenGL.raw.GL._types import *

GL_SPRITE_AXIAL_SGIX: int
GL_SPRITE_AXIS_SGIX: int
GL_SPRITE_EYE_ALIGNED_SGIX: int
GL_SPRITE_MODE_SGIX: int
GL_SPRITE_OBJECT_ALIGNED_SGIX: int
GL_SPRITE_SGIX: int
GL_SPRITE_TRANSLATION_SGIX: int

def glSpriteParameterfSGIX(pname: int, param: float) -> None: ...
def glSpriteParameterfvSGIX(pname: int, params: FloatArray) -> None: ...
def glSpriteParameteriSGIX(pname: int, param: int) -> None: ...
def glSpriteParameterivSGIX(pname: int, params: IntArray) -> None: ...

def glInitSpriteSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
