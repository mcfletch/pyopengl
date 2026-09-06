"""OpenGL.GLES1.OES.point_size_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLES1._types import *

GL_POINT_SIZE_ARRAY_BUFFER_BINDING_OES: int
GL_POINT_SIZE_ARRAY_OES: int
GL_POINT_SIZE_ARRAY_POINTER_OES: int
GL_POINT_SIZE_ARRAY_STRIDE_OES: int
GL_POINT_SIZE_ARRAY_TYPE_OES: int

def glPointSizePointerOES(type: int, stride: int, pointer: AnyArray) -> None: ...

def glInitPointSizeArrayOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
