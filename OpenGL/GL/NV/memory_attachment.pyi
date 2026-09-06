"""OpenGL.GL.NV.memory_attachment -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GL._types import *

GL_ATTACHED_MEMORY_OBJECT_NV: int
GL_ATTACHED_MEMORY_OFFSET_NV: int
GL_DETACHED_BUFFERS_NV: int
GL_DETACHED_MEMORY_INCARNATION_NV: int
GL_DETACHED_TEXTURES_NV: int
GL_MAX_DETACHED_BUFFERS_NV: int
GL_MAX_DETACHED_TEXTURES_NV: int
GL_MEMORY_ATTACHABLE_ALIGNMENT_NV: int
GL_MEMORY_ATTACHABLE_NV: int
GL_MEMORY_ATTACHABLE_SIZE_NV: int

def glBufferAttachMemoryNV(target: int, memory: int, offset: int) -> None: ...
def glGetMemoryObjectDetachedResourcesuivNV(memory: int, pname: int, first: int, count: int, params: UIntArray) -> None: ...
def glNamedBufferAttachMemoryNV(buffer: int, memory: int, offset: int) -> None: ...
def glResetMemoryObjectParameterNV(memory: int, pname: int) -> None: ...
def glTexAttachMemoryNV(target: int, memory: int, offset: int) -> None: ...
def glTextureAttachMemoryNV(texture: int, memory: int, offset: int) -> None: ...

def glInitMemoryAttachmentNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
