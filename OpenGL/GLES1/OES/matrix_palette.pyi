"""OpenGL.GLES1.OES.matrix_palette -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLES1._types import *

GL_CURRENT_PALETTE_MATRIX_OES: int
GL_MATRIX_INDEX_ARRAY_BUFFER_BINDING_OES: int
GL_MATRIX_INDEX_ARRAY_OES: int
GL_MATRIX_INDEX_ARRAY_POINTER_OES: int
GL_MATRIX_INDEX_ARRAY_SIZE_OES: int
GL_MATRIX_INDEX_ARRAY_STRIDE_OES: int
GL_MATRIX_INDEX_ARRAY_TYPE_OES: int
GL_MATRIX_PALETTE_OES: int
GL_MAX_PALETTE_MATRICES_OES: int
GL_MAX_VERTEX_UNITS_OES: int
GL_WEIGHT_ARRAY_BUFFER_BINDING_OES: int
GL_WEIGHT_ARRAY_OES: int
GL_WEIGHT_ARRAY_POINTER_OES: int
GL_WEIGHT_ARRAY_SIZE_OES: int
GL_WEIGHT_ARRAY_STRIDE_OES: int
GL_WEIGHT_ARRAY_TYPE_OES: int

def glCurrentPaletteMatrixOES(matrixpaletteindex: int) -> None: ...
def glLoadPaletteFromModelViewMatrixOES() -> None: ...
def glMatrixIndexPointerOES(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glWeightPointerOES(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...

def glInitMatrixPaletteOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
