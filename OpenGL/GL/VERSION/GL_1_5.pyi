"""OpenGL.GL.VERSION.GL_1_5 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_ARRAY_BUFFER: int
GL_ARRAY_BUFFER_BINDING: int
GL_BUFFER_ACCESS: int
GL_BUFFER_MAPPED: int
GL_BUFFER_MAP_POINTER: int
GL_BUFFER_SIZE: int
GL_BUFFER_USAGE: int
GL_COLOR_ARRAY_BUFFER_BINDING: int
GL_CURRENT_FOG_COORD: int
GL_CURRENT_QUERY: int
GL_DYNAMIC_COPY: int
GL_DYNAMIC_DRAW: int
GL_DYNAMIC_READ: int
GL_EDGE_FLAG_ARRAY_BUFFER_BINDING: int
GL_ELEMENT_ARRAY_BUFFER: int
GL_ELEMENT_ARRAY_BUFFER_BINDING: int
GL_FOG_COORD: int
GL_FOG_COORDINATE_ARRAY_BUFFER_BINDING: int
GL_FOG_COORD_ARRAY: int
GL_FOG_COORD_ARRAY_BUFFER_BINDING: int
GL_FOG_COORD_ARRAY_POINTER: int
GL_FOG_COORD_ARRAY_STRIDE: int
GL_FOG_COORD_ARRAY_TYPE: int
GL_FOG_COORD_SRC: int
GL_INDEX_ARRAY_BUFFER_BINDING: int
GL_NORMAL_ARRAY_BUFFER_BINDING: int
GL_QUERY_COUNTER_BITS: int
GL_QUERY_RESULT: int
GL_QUERY_RESULT_AVAILABLE: int
GL_READ_ONLY: int
GL_READ_WRITE: int
GL_SAMPLES_PASSED: int
GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING: int
GL_SRC0_ALPHA: int
GL_SRC0_RGB: int
GL_SRC1_ALPHA: int
GL_SRC1_RGB: int
GL_SRC2_ALPHA: int
GL_SRC2_RGB: int
GL_STATIC_COPY: int
GL_STATIC_DRAW: int
GL_STATIC_READ: int
GL_STREAM_COPY: int
GL_STREAM_DRAW: int
GL_STREAM_READ: int
GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING: int
GL_VERTEX_ARRAY_BUFFER_BINDING: int
GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING: int
GL_WEIGHT_ARRAY_BUFFER_BINDING: int
GL_WRITE_ONLY: int

def glBeginQuery(target: int, id: int) -> None: ...
def glBindBuffer(target: int, buffer: int) -> None: ...
def glBufferData(target: int, size: int, data: AnyArray, usage: int) -> None: ...
def glBufferSubData(target: int, offset: int, size: int, data: AnyArray) -> None: ...
def glDeleteBuffers(n: int, buffers: UIntArray) -> None: ...
def glDeleteQueries(n: int, ids: UIntArray) -> None: ...
def glEndQuery(target: int) -> None: ...
def glGenBuffers(n: int, buffers: UIntArray | None = None) -> UIntArrayResult: ...
def glGenQueries(n: int, ids: UIntArray | None = None) -> UIntArrayResult: ...
def glGetBufferParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetBufferPointerv(target: int, pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glGetBufferSubData(target: int, offset: int, size: int, data: AnyArray | None = None) -> AnyArrayResult: ...
def glGetQueryObjectiv(id: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetQueryObjectuiv(id: int, pname: int, params: UIntArray | None = None) -> UIntArrayResult: ...
def glGetQueryiv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glIsBuffer(buffer: int) -> int: ...
def glIsQuery(id: int) -> int: ...
def glMapBuffer(target: int, access: int) -> int | None: ...
def glUnmapBuffer(target: int) -> int: ...

def glInitGl15VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
