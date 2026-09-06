"""OpenGL.GL.NV.pixel_data_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_READ_PIXEL_DATA_RANGE_LENGTH_NV: int
GL_READ_PIXEL_DATA_RANGE_NV: int
GL_READ_PIXEL_DATA_RANGE_POINTER_NV: int
GL_WRITE_PIXEL_DATA_RANGE_LENGTH_NV: int
GL_WRITE_PIXEL_DATA_RANGE_NV: int
GL_WRITE_PIXEL_DATA_RANGE_POINTER_NV: int

def glFlushPixelDataRangeNV(target: int) -> None: ...
def glPixelDataRangeNV(target: int, length: int, pointer: AnyArray) -> None: ...

def glInitPixelDataRangeNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
