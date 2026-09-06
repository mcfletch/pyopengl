"""OpenGL.GL.ARB.copy_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_COPY_READ_BUFFER: int
GL_COPY_WRITE_BUFFER: int

def glCopyBufferSubData(readTarget: int, writeTarget: int, readOffset: int, writeOffset: int, size: int) -> None: ...

def glInitCopyBufferARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
