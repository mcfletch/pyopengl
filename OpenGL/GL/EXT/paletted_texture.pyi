"""OpenGL.GL.EXT.paletted_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_COLOR_INDEX12_EXT: int
GL_COLOR_INDEX16_EXT: int
GL_COLOR_INDEX1_EXT: int
GL_COLOR_INDEX2_EXT: int
GL_COLOR_INDEX4_EXT: int
GL_COLOR_INDEX8_EXT: int
GL_TEXTURE_INDEX_SIZE_EXT: int

def glColorTableEXT(target: int, internalFormat: int, width: int, format: int, type: int, table: AnyArray) -> None: ...
def glGetColorTableEXT(target: int, format: int, type: int, data: AnyArray | None = None) -> AnyArrayResult: ...
def glGetColorTableParameterfvEXT(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetColorTableParameterivEXT(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...

def glInitPalettedTextureEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
