"""OpenGL.GL.ARB.transpose_matrix -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import DoubleArray, FloatArray

from OpenGL.raw.GL._types import *

GL_TRANSPOSE_COLOR_MATRIX_ARB: int
GL_TRANSPOSE_MODELVIEW_MATRIX_ARB: int
GL_TRANSPOSE_PROJECTION_MATRIX_ARB: int
GL_TRANSPOSE_TEXTURE_MATRIX_ARB: int

def glLoadTransposeMatrixdARB(m: DoubleArray) -> None: ...
def glLoadTransposeMatrixfARB(m: FloatArray) -> None: ...
def glMultTransposeMatrixdARB(m: DoubleArray) -> None: ...
def glMultTransposeMatrixfARB(m: FloatArray) -> None: ...

def glInitTransposeMatrixARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
