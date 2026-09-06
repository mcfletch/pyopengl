"""OpenGL.GL.ARB.vertex_buffer_object -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ARRAY_BUFFER_ARB: int
GL_ARRAY_BUFFER_BINDING_ARB: int
GL_BUFFER_ACCESS_ARB: int
GL_BUFFER_MAPPED_ARB: int
GL_BUFFER_MAP_POINTER_ARB: int
GL_BUFFER_SIZE_ARB: int
GL_BUFFER_USAGE_ARB: int
GL_COLOR_ARRAY_BUFFER_BINDING_ARB: int
GL_DYNAMIC_COPY_ARB: int
GL_DYNAMIC_DRAW_ARB: int
GL_DYNAMIC_READ_ARB: int
GL_EDGE_FLAG_ARRAY_BUFFER_BINDING_ARB: int
GL_ELEMENT_ARRAY_BUFFER_ARB: int
GL_ELEMENT_ARRAY_BUFFER_BINDING_ARB: int
GL_FOG_COORDINATE_ARRAY_BUFFER_BINDING_ARB: int
GL_INDEX_ARRAY_BUFFER_BINDING_ARB: int
GL_NORMAL_ARRAY_BUFFER_BINDING_ARB: int
GL_READ_ONLY_ARB: int
GL_READ_WRITE_ARB: int
GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING_ARB: int
GL_STATIC_COPY_ARB: int
GL_STATIC_DRAW_ARB: int
GL_STATIC_READ_ARB: int
GL_STREAM_COPY_ARB: int
GL_STREAM_DRAW_ARB: int
GL_STREAM_READ_ARB: int
GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING_ARB: int
GL_VERTEX_ARRAY_BUFFER_BINDING_ARB: int
GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING_ARB: int
GL_WEIGHT_ARRAY_BUFFER_BINDING_ARB: int
GL_WRITE_ONLY_ARB: int

def glBindBufferARB(target: int, buffer: int) -> None: ...
def glBufferDataARB(target: int, size: int, data: AnyArray, usage: int) -> None: ...
def glBufferSubDataARB(target: int, offset: int, size: int, data: AnyArray) -> None: ...
def glDeleteBuffersARB(n: int, buffers: UIntArray) -> None: ...
def glGenBuffersARB(n: int, buffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGetBufferParameterivARB(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetBufferPointervARB(target: int, pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glGetBufferSubDataARB(target: int, offset: int, size: int, data: AnyArray | None = None) -> AnyArrayResult: ...
def glIsBufferARB(buffer: int) -> int: ...
def glMapBufferARB(target: int, access: int) -> int | None: ...
def glUnmapBufferARB(target: int) -> int: ...

def glInitVertexBufferObjectARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
