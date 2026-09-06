"""OpenGL.GLES2.OES.mapbuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLES2._types import *

GL_BUFFER_ACCESS_OES: int
GL_BUFFER_MAPPED_OES: int
GL_BUFFER_MAP_POINTER_OES: int
GL_WRITE_ONLY_OES: int

def glGetBufferPointervOES(target: int, pname: int, params: AnyArray) -> None: ...
def glMapBufferOES(target: int, access: int) -> int | None: ...
def glUnmapBufferOES(target: int) -> int: ...

def glInitMapbufferOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
