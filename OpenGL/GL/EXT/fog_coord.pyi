"""OpenGL.GL.EXT.fog_coord -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, DoubleArray, FloatArray

from OpenGL.raw.GL._types import *

GL_CURRENT_FOG_COORDINATE_EXT: int
GL_FOG_COORDINATE_ARRAY_EXT: int
GL_FOG_COORDINATE_ARRAY_POINTER_EXT: int
GL_FOG_COORDINATE_ARRAY_STRIDE_EXT: int
GL_FOG_COORDINATE_ARRAY_TYPE_EXT: int
GL_FOG_COORDINATE_EXT: int
GL_FOG_COORDINATE_SOURCE_EXT: int
GL_FRAGMENT_DEPTH_EXT: int

def glFogCoordPointerEXT(type: int, stride: int, pointer: AnyArray) -> None: ...
def glFogCoorddEXT(coord: float) -> None: ...
def glFogCoorddvEXT(coord: DoubleArray) -> None: ...
def glFogCoordfEXT(coord: float) -> None: ...
def glFogCoordfvEXT(coord: FloatArray) -> None: ...

def glInitFogCoordEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
