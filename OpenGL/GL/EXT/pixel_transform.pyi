"""OpenGL.GL.EXT.pixel_transform -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_AVERAGE_EXT: int
GL_CUBIC_EXT: int
GL_MAX_PIXEL_TRANSFORM_2D_STACK_DEPTH_EXT: int
GL_PIXEL_CUBIC_WEIGHT_EXT: int
GL_PIXEL_MAG_FILTER_EXT: int
GL_PIXEL_MIN_FILTER_EXT: int
GL_PIXEL_TRANSFORM_2D_EXT: int
GL_PIXEL_TRANSFORM_2D_MATRIX_EXT: int
GL_PIXEL_TRANSFORM_2D_STACK_DEPTH_EXT: int

def glGetPixelTransformParameterfvEXT(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetPixelTransformParameterivEXT(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glPixelTransformParameterfEXT(target: int, pname: int, param: float) -> None: ...
def glPixelTransformParameterfvEXT(target: int, pname: int, params: FloatArray) -> None: ...
def glPixelTransformParameteriEXT(target: int, pname: int, param: int) -> None: ...
def glPixelTransformParameterivEXT(target: int, pname: int, params: IntArray) -> None: ...

def glInitPixelTransformEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
