"""OpenGL.GL.ARB.matrix_palette -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, UByteArray, UIntArray, UShortArray

from OpenGL.raw.GL._types import *

GL_CURRENT_MATRIX_INDEX_ARB: int
GL_CURRENT_PALETTE_MATRIX_ARB: int
GL_MATRIX_INDEX_ARRAY_ARB: int
GL_MATRIX_INDEX_ARRAY_POINTER_ARB: int
GL_MATRIX_INDEX_ARRAY_SIZE_ARB: int
GL_MATRIX_INDEX_ARRAY_STRIDE_ARB: int
GL_MATRIX_INDEX_ARRAY_TYPE_ARB: int
GL_MATRIX_PALETTE_ARB: int
GL_MAX_MATRIX_PALETTE_STACK_DEPTH_ARB: int
GL_MAX_PALETTE_MATRICES_ARB: int

def glCurrentPaletteMatrixARB(index: int) -> None: ...
def glMatrixIndexPointerARB(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glMatrixIndexubvARB(size: int, indices: UByteArray) -> None: ...
def glMatrixIndexuivARB(size: int, indices: UIntArray) -> None: ...
def glMatrixIndexusvARB(size: int, indices: UShortArray) -> None: ...

def glInitMatrixPaletteARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
