"""OpenGL.GLES2.OES.texture_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_IMAGE_BUFFER_OES: int
GL_INT_IMAGE_BUFFER_OES: int
GL_INT_SAMPLER_BUFFER_OES: int
GL_MAX_TEXTURE_BUFFER_SIZE_OES: int
GL_SAMPLER_BUFFER_OES: int
GL_TEXTURE_BINDING_BUFFER_OES: int
GL_TEXTURE_BUFFER_BINDING_OES: int
GL_TEXTURE_BUFFER_DATA_STORE_BINDING_OES: int
GL_TEXTURE_BUFFER_OES: int
GL_TEXTURE_BUFFER_OFFSET_ALIGNMENT_OES: int
GL_TEXTURE_BUFFER_OFFSET_OES: int
GL_TEXTURE_BUFFER_SIZE_OES: int
GL_UNSIGNED_INT_IMAGE_BUFFER_OES: int
GL_UNSIGNED_INT_SAMPLER_BUFFER_OES: int

def glTexBufferOES(target: int, internalformat: int, buffer: int) -> None: ...
def glTexBufferRangeOES(target: int, internalformat: int, buffer: int, offset: int, size: int) -> None: ...

def glInitTextureBufferOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
