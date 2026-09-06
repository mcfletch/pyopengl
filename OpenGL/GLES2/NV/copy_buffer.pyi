"""OpenGL.GLES2.NV.copy_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_COPY_READ_BUFFER_NV: int
GL_COPY_WRITE_BUFFER_NV: int

def glCopyBufferSubDataNV(readTarget: int, writeTarget: int, readOffset: int, writeOffset: int, size: int) -> None: ...

def glInitCopyBufferNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
