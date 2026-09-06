"""OpenGL.GLES2.EXT.texture_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_IMAGE_BUFFER_EXT: int
GL_INT_IMAGE_BUFFER_EXT: int
GL_INT_SAMPLER_BUFFER_EXT: int
GL_MAX_TEXTURE_BUFFER_SIZE_EXT: int
GL_SAMPLER_BUFFER_EXT: int
GL_TEXTURE_BINDING_BUFFER_EXT: int
GL_TEXTURE_BUFFER_BINDING_EXT: int
GL_TEXTURE_BUFFER_DATA_STORE_BINDING_EXT: int
GL_TEXTURE_BUFFER_EXT: int
GL_TEXTURE_BUFFER_OFFSET_ALIGNMENT_EXT: int
GL_TEXTURE_BUFFER_OFFSET_EXT: int
GL_TEXTURE_BUFFER_SIZE_EXT: int
GL_UNSIGNED_INT_IMAGE_BUFFER_EXT: int
GL_UNSIGNED_INT_SAMPLER_BUFFER_EXT: int

def glTexBufferEXT(target: int, internalformat: int, buffer: int) -> None: ...
def glTexBufferRangeEXT(target: int, internalformat: int, buffer: int, offset: int, size: int) -> None: ...

def glInitTextureBufferEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
