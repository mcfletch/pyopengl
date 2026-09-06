"""OpenGL.GL.APPLE.flush_buffer_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BUFFER_FLUSHING_UNMAP_APPLE: int
GL_BUFFER_SERIALIZED_MODIFY_APPLE: int

def glBufferParameteriAPPLE(target: int, pname: int, param: int) -> None: ...
def glFlushMappedBufferRangeAPPLE(target: int, offset: int, size: int) -> None: ...

def glInitFlushBufferRangeAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
