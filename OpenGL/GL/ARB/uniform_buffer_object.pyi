"""OpenGL.GL.ARB.uniform_buffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ACTIVE_UNIFORM_BLOCKS: int
GL_ACTIVE_UNIFORM_BLOCK_MAX_NAME_LENGTH: int
GL_INVALID_INDEX: int
GL_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS: int
GL_MAX_COMBINED_GEOMETRY_UNIFORM_COMPONENTS: int
GL_MAX_COMBINED_UNIFORM_BLOCKS: int
GL_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS: int
GL_MAX_FRAGMENT_UNIFORM_BLOCKS: int
GL_MAX_GEOMETRY_UNIFORM_BLOCKS: int
GL_MAX_UNIFORM_BLOCK_SIZE: int
GL_MAX_UNIFORM_BUFFER_BINDINGS: int
GL_MAX_VERTEX_UNIFORM_BLOCKS: int
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

def glBindBufferBase(target: int, index: int, buffer: int) -> None: ...
def glBindBufferRange(target: int, index: int, buffer: int, offset: int, size: int) -> None: ...
def glGetActiveUniformBlockName(program: int, uniformBlockIndex: int, bufSize: int, length: IntArray | None = None, uniformBlockName: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult]: ...
def glGetActiveUniformBlockiv(program: int, uniformBlockIndex: int, pname: int, params: IntArray) -> None: ...
def glGetActiveUniformName(program: int, uniformIndex: int, bufSize: int, length: IntArray | None = None, uniformName: ByteArray | None = None) -> tuple[IntArrayResult, ByteArrayResult]: ...
def glGetActiveUniformsiv(program: int, uniformCount: int, uniformIndices: UIntArray, pname: int, params: IntArray) -> None: ...
def glGetIntegeri_v(target: int, index: int, data: IntArray | None = None) -> IntArrayResult: ...
def glGetUniformBlockIndex(program: int, uniformBlockName: ByteArray) -> int: ...
def glGetUniformIndices(program: int, uniformCount: int, uniformNames: AnyArray, uniformIndices: UIntArray | None = None) -> UIntArrayResult: ...
def glUniformBlockBinding(program: int, uniformBlockIndex: int, uniformBlockBinding: int) -> None: ...

def glInitUniformBufferObjectARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
