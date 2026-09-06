"""OpenGL.GL.EXT.texture_buffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MAX_TEXTURE_BUFFER_SIZE_EXT: int
GL_TEXTURE_BINDING_BUFFER_EXT: int
GL_TEXTURE_BUFFER_DATA_STORE_BINDING_EXT: int
GL_TEXTURE_BUFFER_EXT: int
GL_TEXTURE_BUFFER_FORMAT_EXT: int

def glTexBufferEXT(target: int, internalformat: int, buffer: int) -> None: ...

def glInitTextureBufferObjectEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
