"""OpenGL.GL.ARB.texture_buffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_TEXTURE_BUFFER_SIZE_ARB: int
GL_TEXTURE_BINDING_BUFFER_ARB: int
GL_TEXTURE_BUFFER_ARB: int
GL_TEXTURE_BUFFER_DATA_STORE_BINDING_ARB: int
GL_TEXTURE_BUFFER_FORMAT_ARB: int

def glTexBufferARB(target: int, internalformat: int, buffer: int) -> None: ...

def glInitTextureBufferObjectARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
