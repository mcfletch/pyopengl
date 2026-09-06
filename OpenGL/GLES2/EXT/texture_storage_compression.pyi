"""OpenGL.GLES2.EXT.texture_storage_compression -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GLES2._types import *

GL_NUM_SURFACE_COMPRESSION_FIXED_RATES_EXT: int
GL_SURFACE_COMPRESSION_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_10BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_11BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_12BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_1BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_2BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_3BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_4BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_5BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_6BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_7BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_8BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_9BPC_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_DEFAULT_EXT: int
GL_SURFACE_COMPRESSION_FIXED_RATE_NONE_EXT: int

def glTexStorageAttribs2DEXT(target: int, levels: int, internalformat: int, width: int, height: int, attrib_list: IntArray) -> None: ...
def glTexStorageAttribs3DEXT(target: int, levels: int, internalformat: int, width: int, height: int, depth: int, attrib_list: IntArray) -> None: ...

def glInitTextureStorageCompressionEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
