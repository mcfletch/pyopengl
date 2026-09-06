"""OpenGL.GL.EXT.vertex_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, UByteArray

from OpenGL.raw.GL._types import *

GL_COLOR_ARRAY_COUNT_EXT: int
GL_COLOR_ARRAY_EXT: int
GL_COLOR_ARRAY_POINTER_EXT: int
GL_COLOR_ARRAY_SIZE_EXT: int
GL_COLOR_ARRAY_STRIDE_EXT: int
GL_COLOR_ARRAY_TYPE_EXT: int
GL_EDGE_FLAG_ARRAY_COUNT_EXT: int
GL_EDGE_FLAG_ARRAY_EXT: int
GL_EDGE_FLAG_ARRAY_POINTER_EXT: int
GL_EDGE_FLAG_ARRAY_STRIDE_EXT: int
GL_INDEX_ARRAY_COUNT_EXT: int
GL_INDEX_ARRAY_EXT: int
GL_INDEX_ARRAY_POINTER_EXT: int
GL_INDEX_ARRAY_STRIDE_EXT: int
GL_INDEX_ARRAY_TYPE_EXT: int
GL_NORMAL_ARRAY_COUNT_EXT: int
GL_NORMAL_ARRAY_EXT: int
GL_NORMAL_ARRAY_POINTER_EXT: int
GL_NORMAL_ARRAY_STRIDE_EXT: int
GL_NORMAL_ARRAY_TYPE_EXT: int
GL_TEXTURE_COORD_ARRAY_COUNT_EXT: int
GL_TEXTURE_COORD_ARRAY_EXT: int
GL_TEXTURE_COORD_ARRAY_POINTER_EXT: int
GL_TEXTURE_COORD_ARRAY_SIZE_EXT: int
GL_TEXTURE_COORD_ARRAY_STRIDE_EXT: int
GL_TEXTURE_COORD_ARRAY_TYPE_EXT: int
GL_VERTEX_ARRAY_COUNT_EXT: int
GL_VERTEX_ARRAY_EXT: int
GL_VERTEX_ARRAY_POINTER_EXT: int
GL_VERTEX_ARRAY_SIZE_EXT: int
GL_VERTEX_ARRAY_STRIDE_EXT: int
GL_VERTEX_ARRAY_TYPE_EXT: int

def glArrayElementEXT(i: int) -> None: ...
def glColorPointerEXT(size: int, type: int, stride: int, count: int, pointer: AnyArray) -> None: ...
def glDrawArraysEXT(mode: int, first: int, count: int) -> None: ...
def glEdgeFlagPointerEXT(stride: int, count: int, pointer: UByteArray) -> None: ...
def glGetPointervEXT(pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glIndexPointerEXT(type: int, stride: int, count: int, pointer: AnyArray) -> None: ...
def glNormalPointerEXT(type: int, stride: int, count: int, pointer: AnyArray) -> None: ...
def glTexCoordPointerEXT(size: int, type: int, stride: int, count: int, pointer: AnyArray) -> None: ...
def glVertexPointerEXT(size: int, type: int, stride: int, count: int, pointer: AnyArray) -> None: ...

def glInitVertexArrayEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
