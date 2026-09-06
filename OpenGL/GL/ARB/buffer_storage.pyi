"""OpenGL.GL.ARB.buffer_storage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_BUFFER_IMMUTABLE_STORAGE: int
GL_BUFFER_STORAGE_FLAGS: int
GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT: int
GL_CLIENT_STORAGE_BIT: int
GL_DYNAMIC_STORAGE_BIT: int
GL_MAP_COHERENT_BIT: int
GL_MAP_PERSISTENT_BIT: int
GL_MAP_READ_BIT: int
GL_MAP_WRITE_BIT: int

def glBufferStorage(target: int, size: int, data: AnyArray, flags: int) -> None: ...

def glInitBufferStorageARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
