"""OpenGL.GLES2.EXT.buffer_storage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLES2._types import *

GL_BUFFER_IMMUTABLE_STORAGE_EXT: int
GL_BUFFER_STORAGE_FLAGS_EXT: int
GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT_EXT: int
GL_CLIENT_STORAGE_BIT_EXT: int
GL_DYNAMIC_STORAGE_BIT_EXT: int
GL_MAP_COHERENT_BIT_EXT: int
GL_MAP_PERSISTENT_BIT_EXT: int
GL_MAP_READ_BIT: int
GL_MAP_WRITE_BIT: int

def glBufferStorageEXT(target: int, size: int, data: AnyArray, flags: int) -> None: ...

def glInitBufferStorageEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
