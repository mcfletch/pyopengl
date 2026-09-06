"""OpenGL.GL.EXT.semaphore_fd -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_HANDLE_TYPE_OPAQUE_FD_EXT: int

def glImportSemaphoreFdEXT(semaphore: int, handleType: int, fd: int) -> None: ...

def glInitSemaphoreFdEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
