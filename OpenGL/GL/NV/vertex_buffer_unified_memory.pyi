"""OpenGL.GL.NV.vertex_buffer_unified_memory -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UInt64Array, UInt64ArrayResult

from OpenGL.raw.GL._types import *

GL_COLOR_ARRAY_ADDRESS_NV: int
GL_COLOR_ARRAY_LENGTH_NV: int
GL_DRAW_INDIRECT_ADDRESS_NV: int
GL_DRAW_INDIRECT_LENGTH_NV: int
GL_DRAW_INDIRECT_UNIFIED_NV: int
GL_EDGE_FLAG_ARRAY_ADDRESS_NV: int
GL_EDGE_FLAG_ARRAY_LENGTH_NV: int
GL_ELEMENT_ARRAY_ADDRESS_NV: int
GL_ELEMENT_ARRAY_LENGTH_NV: int
GL_ELEMENT_ARRAY_UNIFIED_NV: int
GL_FOG_COORD_ARRAY_ADDRESS_NV: int
GL_FOG_COORD_ARRAY_LENGTH_NV: int
GL_INDEX_ARRAY_ADDRESS_NV: int
GL_INDEX_ARRAY_LENGTH_NV: int
GL_NORMAL_ARRAY_ADDRESS_NV: int
GL_NORMAL_ARRAY_LENGTH_NV: int
GL_SECONDARY_COLOR_ARRAY_ADDRESS_NV: int
GL_SECONDARY_COLOR_ARRAY_LENGTH_NV: int
GL_TEXTURE_COORD_ARRAY_ADDRESS_NV: int
GL_TEXTURE_COORD_ARRAY_LENGTH_NV: int
GL_VERTEX_ARRAY_ADDRESS_NV: int
GL_VERTEX_ARRAY_LENGTH_NV: int
GL_VERTEX_ATTRIB_ARRAY_ADDRESS_NV: int
GL_VERTEX_ATTRIB_ARRAY_LENGTH_NV: int
GL_VERTEX_ATTRIB_ARRAY_UNIFIED_NV: int

def glBufferAddressRangeNV(pname: int, index: int, address: int, length: int) -> None: ...
def glColorFormatNV(size: int, type: int, stride: int) -> None: ...
def glEdgeFlagFormatNV(stride: int) -> None: ...
def glFogCoordFormatNV(type: int, stride: int) -> None: ...
def glGetIntegerui64i_vNV(value: int, index: int, result: UInt64Array | None = None) -> UInt64ArrayResult: ...
def glIndexFormatNV(type: int, stride: int) -> None: ...
def glNormalFormatNV(type: int, stride: int) -> None: ...
def glSecondaryColorFormatNV(size: int, type: int, stride: int) -> None: ...
def glTexCoordFormatNV(size: int, type: int, stride: int) -> None: ...
def glVertexAttribFormatNV(index: int, size: int, type: int, normalized: int, stride: int) -> None: ...
def glVertexAttribIFormatNV(index: int, size: int, type: int, stride: int) -> None: ...
def glVertexFormatNV(size: int, type: int, stride: int) -> None: ...

def glInitVertexBufferUnifiedMemoryNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
