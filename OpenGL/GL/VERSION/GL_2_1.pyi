"""OpenGL.GL.VERSION.GL_2_1 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_COMPRESSED_SLUMINANCE: int
GL_COMPRESSED_SLUMINANCE_ALPHA: int
GL_COMPRESSED_SRGB: int
GL_COMPRESSED_SRGB_ALPHA: int
GL_CURRENT_RASTER_SECONDARY_COLOR: int
GL_FLOAT_MAT2x3: int
GL_FLOAT_MAT2x4: int
GL_FLOAT_MAT3x2: int
GL_FLOAT_MAT3x4: int
GL_FLOAT_MAT4x2: int
GL_FLOAT_MAT4x3: int
GL_PIXEL_PACK_BUFFER: int
GL_PIXEL_PACK_BUFFER_BINDING: int
GL_PIXEL_UNPACK_BUFFER: int
GL_PIXEL_UNPACK_BUFFER_BINDING: int
GL_SLUMINANCE: int
GL_SLUMINANCE8: int
GL_SLUMINANCE8_ALPHA8: int
GL_SLUMINANCE_ALPHA: int
GL_SRGB: int
GL_SRGB8: int
GL_SRGB8_ALPHA8: int
GL_SRGB_ALPHA: int

def glUniformMatrix2x3fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...
def glUniformMatrix2x4fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...
def glUniformMatrix3x2fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...
def glUniformMatrix3x4fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...
def glUniformMatrix4x2fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...
def glUniformMatrix4x3fv(location: int, count: int, transpose: int, value: FloatArray) -> None: ...

def glInitGl21VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
