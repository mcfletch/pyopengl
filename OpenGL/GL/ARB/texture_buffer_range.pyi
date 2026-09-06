"""OpenGL.GL.ARB.texture_buffer_range -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_TEXTURE_BUFFER_OFFSET: int
GL_TEXTURE_BUFFER_OFFSET_ALIGNMENT: int
GL_TEXTURE_BUFFER_SIZE: int

def glTexBufferRange(target: int, internalformat: int, buffer: int, offset: int, size: int) -> None: ...

def glInitTextureBufferRangeARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
