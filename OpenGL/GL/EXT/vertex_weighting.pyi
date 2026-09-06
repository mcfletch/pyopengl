"""OpenGL.GL.EXT.vertex_weighting -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, FloatArray

from OpenGL.raw.GL._types import *

GL_CURRENT_VERTEX_WEIGHT_EXT: int
GL_MODELVIEW0_EXT: int
GL_MODELVIEW0_MATRIX_EXT: int
GL_MODELVIEW0_STACK_DEPTH_EXT: int
GL_MODELVIEW1_EXT: int
GL_MODELVIEW1_MATRIX_EXT: int
GL_MODELVIEW1_STACK_DEPTH_EXT: int
GL_VERTEX_WEIGHTING_EXT: int
GL_VERTEX_WEIGHT_ARRAY_EXT: int
GL_VERTEX_WEIGHT_ARRAY_POINTER_EXT: int
GL_VERTEX_WEIGHT_ARRAY_SIZE_EXT: int
GL_VERTEX_WEIGHT_ARRAY_STRIDE_EXT: int
GL_VERTEX_WEIGHT_ARRAY_TYPE_EXT: int

def glVertexWeightPointerEXT(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glVertexWeightfEXT(weight: float) -> None: ...
def glVertexWeightfvEXT(weight: FloatArray) -> None: ...

def glInitVertexWeightingEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
