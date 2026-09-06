"""OpenGL.GL.VERSION.GL_3_1 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ACTIVE_UNIFORM_BLOCKS: int
GL_ACTIVE_UNIFORM_BLOCK_MAX_NAME_LENGTH: int
GL_COPY_READ_BUFFER: int
GL_COPY_WRITE_BUFFER: int
GL_INT_SAMPLER_2D_RECT: int
GL_INT_SAMPLER_BUFFER: int
GL_INVALID_INDEX: int
GL_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS: int
GL_MAX_COMBINED_GEOMETRY_UNIFORM_COMPONENTS: int
GL_MAX_COMBINED_UNIFORM_BLOCKS: int
GL_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS: int
GL_MAX_FRAGMENT_UNIFORM_BLOCKS: int
GL_MAX_GEOMETRY_UNIFORM_BLOCKS: int
GL_MAX_RECTANGLE_TEXTURE_SIZE: int
GL_MAX_TEXTURE_BUFFER_SIZE: int
GL_MAX_UNIFORM_BLOCK_SIZE: int
GL_MAX_UNIFORM_BUFFER_BINDINGS: int
GL_MAX_VERTEX_UNIFORM_BLOCKS: int
GL_PRIMITIVE_RESTART: int
GL_PRIMITIVE_RESTART_INDEX: int
GL_PROXY_TEXTURE_RECTANGLE: int
GL_R16_SNORM: int
GL_R8_SNORM: int
GL_RG16_SNORM: int
GL_RG8_SNORM: int
GL_RGB16_SNORM: int
GL_RGB8_SNORM: int
GL_RGBA16_SNORM: int
GL_RGBA8_SNORM: int
GL_SAMPLER_2D_RECT: int
GL_SAMPLER_2D_RECT_SHADOW: int
GL_SAMPLER_BUFFER: int
GL_SIGNED_NORMALIZED: int
GL_TEXTURE_BINDING_BUFFER: int
GL_TEXTURE_BINDING_RECTANGLE: int
GL_TEXTURE_BUFFER: int
GL_TEXTURE_BUFFER_DATA_STORE_BINDING: int
GL_TEXTURE_RECTANGLE: int
GL_UNIFORM_ARRAY_STRIDE: int
GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS: int
GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES: int
GL_UNIFORM_BLOCK_BINDING: int
GL_UNIFORM_BLOCK_DATA_SIZE: int
GL_UNIFORM_BLOCK_INDEX: int
GL_UNIFORM_BLOCK_NAME_LENGTH: int
GL_UNIFORM_BLOCK_REFERENCED_BY_FRAGMENT_SHADER: int
GL_UNIFORM_BLOCK_REFERENCED_BY_GEOMETRY_SHADER: int
GL_UNIFORM_BLOCK_REFERENCED_BY_VERTEX_SHADER: int
GL_UNIFORM_BUFFER: int
GL_UNIFORM_BUFFER_BINDING: int
GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT: int
GL_UNIFORM_BUFFER_SIZE: int
GL_UNIFORM_BUFFER_START: int
GL_UNIFORM_IS_ROW_MAJOR: int
GL_UNIFORM_MATRIX_STRIDE: int
GL_UNIFORM_NAME_LENGTH: int
GL_UNIFORM_OFFSET: int
GL_UNIFORM_SIZE: int
GL_UNIFORM_TYPE: int
GL_UNSIGNED_INT_SAMPLER_2D_RECT: int
GL_UNSIGNED_INT_SAMPLER_BUFFER: int

def glBindBufferBase(target: int, index: int, buffer: int) -> None: ...
def glBindBufferRange(target: int, index: int, buffer: int, offset: int, size: int) -> None: ...
def glCopyBufferSubData(readTarget: int, writeTarget: int, readOffset: int, writeOffset: int, size: int) -> None: ...
def glDrawArraysInstanced(mode: int, first: int, count: int, instancecount: int) -> None: ...
def glDrawElementsInstanced(mode: int, count: int, type: int, indices: AnyArray, instancecount: int) -> None: ...
def glGetActiveUniformBlockName(program: int, uniformBlockIndex: int, bufSize: int, length: IntArray | None = None, uniformBlockName: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult]: ...
def glGetActiveUniformBlockiv(program: int, uniformBlockIndex: int, pname: int, params: IntArray) -> None: ...
def glGetActiveUniformName(program: int, uniformIndex: int, bufSize: int, length: IntArray | None = None, uniformName: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult]: ...
def glGetActiveUniformsiv(program: int, uniformCount: int, uniformIndices: UIntArray, pname: int, params: IntArray) -> None: ...
def glGetIntegeri_v(target: int, index: int, data: IntArray | None = None) -> IntArrayResult: ...
def glGetUniformBlockIndex(program: int, uniformBlockName: ByteArray) -> int: ...
def glGetUniformIndices(program: int, uniformCount: int, uniformNames: AnyArray, uniformIndices: UIntArray | None = None) -> UIntArrayResult: ...
def glPrimitiveRestartIndex(index: int) -> None: ...
def glTexBuffer(target: int, internalformat: int, buffer: int) -> None: ...
def glUniformBlockBinding(program: int, uniformBlockIndex: int, uniformBlockBinding: int) -> None: ...

def glInitGl31VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
