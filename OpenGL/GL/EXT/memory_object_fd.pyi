"""OpenGL.GL.EXT.memory_object_fd -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_HANDLE_TYPE_OPAQUE_FD_EXT: int

def glImportMemoryFdEXT(memory: int, size: int, handleType: int, fd: int) -> None: ...

def glInitMemoryObjectFdEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
