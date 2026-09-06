"""OpenGL.GL.IBM.vertex_array_lists -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, UByteArray

from OpenGL.raw.GL._types import *

GL_COLOR_ARRAY_LIST_IBM: int
GL_COLOR_ARRAY_LIST_STRIDE_IBM: int
GL_EDGE_FLAG_ARRAY_LIST_IBM: int
GL_EDGE_FLAG_ARRAY_LIST_STRIDE_IBM: int
GL_FOG_COORDINATE_ARRAY_LIST_IBM: int
GL_FOG_COORDINATE_ARRAY_LIST_STRIDE_IBM: int
GL_INDEX_ARRAY_LIST_IBM: int
GL_INDEX_ARRAY_LIST_STRIDE_IBM: int
GL_NORMAL_ARRAY_LIST_IBM: int
GL_NORMAL_ARRAY_LIST_STRIDE_IBM: int
GL_SECONDARY_COLOR_ARRAY_LIST_IBM: int
GL_SECONDARY_COLOR_ARRAY_LIST_STRIDE_IBM: int
GL_TEXTURE_COORD_ARRAY_LIST_IBM: int
GL_TEXTURE_COORD_ARRAY_LIST_STRIDE_IBM: int
GL_VERTEX_ARRAY_LIST_IBM: int
GL_VERTEX_ARRAY_LIST_STRIDE_IBM: int

def glColorPointerListIBM(size: int, type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glEdgeFlagPointerListIBM(stride: int, pointer: UByteArray, ptrstride: int) -> None: ...
def glFogCoordPointerListIBM(type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glIndexPointerListIBM(type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glNormalPointerListIBM(type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glSecondaryColorPointerListIBM(size: int, type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glTexCoordPointerListIBM(size: int, type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...
def glVertexPointerListIBM(size: int, type: int, stride: int, pointer: AnyArray, ptrstride: int) -> None: ...

def glInitVertexArrayListsIBM() -> bool: ...

def __getattr__(name: str) -> Any: ...
