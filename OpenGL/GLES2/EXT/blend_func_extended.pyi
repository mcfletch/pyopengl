"""OpenGL.GLES2.EXT.blend_func_extended -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import ByteArray

from OpenGL.raw.GLES2._types import *

GL_LOCATION_INDEX_EXT: int
GL_MAX_DUAL_SOURCE_DRAW_BUFFERS_EXT: int
GL_ONE_MINUS_SRC1_ALPHA_EXT: int
GL_ONE_MINUS_SRC1_COLOR_EXT: int
GL_SRC1_ALPHA_EXT: int
GL_SRC1_COLOR_EXT: int
GL_SRC_ALPHA_SATURATE_EXT: int

def glBindFragDataLocationEXT(program: int, color: int, name: ByteArray) -> None: ...
def glBindFragDataLocationIndexedEXT(program: int, colorNumber: int, index: int, name: ByteArray) -> None: ...
def glGetFragDataIndexEXT(program: int, name: ByteArray) -> int: ...
def glGetProgramResourceLocationIndexEXT(program: int, programInterface: int, name: ByteArray) -> int: ...

def glInitBlendFuncExtendedEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
