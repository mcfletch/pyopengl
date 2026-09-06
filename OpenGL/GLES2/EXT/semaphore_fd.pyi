"""OpenGL.GLES2.EXT.semaphore_fd -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_HANDLE_TYPE_OPAQUE_FD_EXT: int

def glImportSemaphoreFdEXT(semaphore: int, handleType: int, fd: int) -> None: ...

def glInitSemaphoreFdEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
