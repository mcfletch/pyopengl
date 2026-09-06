"""OpenGL.GL.ARB.map_buffer_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAP_FLUSH_EXPLICIT_BIT: int
GL_MAP_INVALIDATE_BUFFER_BIT: int
GL_MAP_INVALIDATE_RANGE_BIT: int
GL_MAP_READ_BIT: int
GL_MAP_UNSYNCHRONIZED_BIT: int
GL_MAP_WRITE_BIT: int

def glFlushMappedBufferRange(target: int, offset: int, length: int) -> None: ...
def glMapBufferRange(target: int, offset: int, length: int, access: int) -> int | None: ...

def glInitMapBufferRangeARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
