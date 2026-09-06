"""OpenGL.GLES1.EXT.map_buffer_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES1._types import *

GL_MAP_FLUSH_EXPLICIT_BIT_EXT: int
GL_MAP_INVALIDATE_BUFFER_BIT_EXT: int
GL_MAP_INVALIDATE_RANGE_BIT_EXT: int
GL_MAP_READ_BIT_EXT: int
GL_MAP_UNSYNCHRONIZED_BIT_EXT: int
GL_MAP_WRITE_BIT_EXT: int

def glFlushMappedBufferRangeEXT(target: int, offset: int, length: int) -> None: ...
def glMapBufferRangeEXT(target: int, offset: int, length: int, access: int) -> int | None: ...

def glInitMapBufferRangeEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
