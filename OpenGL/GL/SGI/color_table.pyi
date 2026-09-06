"""OpenGL.GL.SGI.color_table -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_COLOR_TABLE_ALPHA_SIZE_SGI: int
GL_COLOR_TABLE_BIAS_SGI: int
GL_COLOR_TABLE_BLUE_SIZE_SGI: int
GL_COLOR_TABLE_FORMAT_SGI: int
GL_COLOR_TABLE_GREEN_SIZE_SGI: int
GL_COLOR_TABLE_INTENSITY_SIZE_SGI: int
GL_COLOR_TABLE_LUMINANCE_SIZE_SGI: int
GL_COLOR_TABLE_RED_SIZE_SGI: int
GL_COLOR_TABLE_SCALE_SGI: int
GL_COLOR_TABLE_SGI: int
GL_COLOR_TABLE_WIDTH_SGI: int
GL_POST_COLOR_MATRIX_COLOR_TABLE_SGI: int
GL_POST_CONVOLUTION_COLOR_TABLE_SGI: int
GL_PROXY_COLOR_TABLE_SGI: int
GL_PROXY_POST_COLOR_MATRIX_COLOR_TABLE_SGI: int
GL_PROXY_POST_CONVOLUTION_COLOR_TABLE_SGI: int

def glColorTableParameterfvSGI(target: int, pname: int, params: FloatArray) -> None: ...
def glColorTableParameterivSGI(target: int, pname: int, params: IntArray) -> None: ...
def glColorTableSGI(target: int, internalformat: int, width: int, format: int, type: int, table: AnyArray) -> None: ...
def glCopyColorTableSGI(target: int, internalformat: int, x: int, y: int, width: int) -> None: ...
def glGetColorTableParameterfvSGI(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetColorTableParameterivSGI(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetColorTableSGI(target: int, format: int, type: int, table: AnyArray | None = None) -> AnyArrayResult: ...

def glInitColorTableSGI() -> bool: ...

def __getattr__(name: str) -> Any: ...
