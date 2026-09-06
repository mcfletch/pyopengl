"""OpenGL.GL.VERSION.GL_4_4 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, Int64Array, IntArray, UInt64Array, UIntArray

from OpenGL.raw.GL._types import *

GL_BUFFER_IMMUTABLE_STORAGE: int
GL_BUFFER_STORAGE_FLAGS: int
GL_CLEAR_TEXTURE: int
GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT: int
GL_CLIENT_STORAGE_BIT: int
GL_DYNAMIC_STORAGE_BIT: int
GL_LOCATION_COMPONENT: int
GL_MAP_COHERENT_BIT: int
GL_MAP_PERSISTENT_BIT: int
GL_MAP_READ_BIT: int
GL_MAP_WRITE_BIT: int
GL_MAX_VERTEX_ATTRIB_STRIDE: int
GL_MIRROR_CLAMP_TO_EDGE: int
GL_PRIMITIVE_RESTART_FOR_PATCHES_SUPPORTED: int
GL_QUERY_BUFFER: int
GL_QUERY_BUFFER_BARRIER_BIT: int
GL_QUERY_BUFFER_BINDING: int
GL_QUERY_RESULT_NO_WAIT: int
GL_STENCIL_INDEX: int
GL_STENCIL_INDEX8: int
GL_TEXTURE_BUFFER_BINDING: int
GL_TRANSFORM_FEEDBACK_BUFFER: int
GL_TRANSFORM_FEEDBACK_BUFFER_INDEX: int
GL_TRANSFORM_FEEDBACK_BUFFER_STRIDE: int
GL_UNSIGNED_INT_10F_11F_11F_REV: int

def glBindBuffersBase(target: int, first: int, count: int, buffers: UIntArray) -> None: ...
def glBindBuffersRange(target: int, first: int, count: int, buffers: UIntArray, offsets: Int64Array, sizes: UInt64Array) -> None: ...
def glBindImageTextures(first: int, count: int, textures: UIntArray) -> None: ...
def glBindSamplers(first: int, count: int, samplers: UIntArray) -> None: ...
def glBindTextures(first: int, count: int, textures: UIntArray) -> None: ...
def glBindVertexBuffers(first: int, count: int, buffers: UIntArray, offsets: Int64Array, strides: IntArray) -> None: ...
def glBufferStorage(target: int, size: int, data: AnyArray, flags: int) -> None: ...
def glClearTexImage(texture: int, level: int, format: int, type: int, data: AnyArray) -> None: ...
def glClearTexSubImage(texture: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, type: int, data: AnyArray) -> None: ...

def glInitGl44VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
