"""OpenGL.GL.NV.query_resource -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GL._types import *

GL_QUERY_RESOURCE_BUFFEROBJECT_NV: int
GL_QUERY_RESOURCE_MEMTYPE_VIDMEM_NV: int
GL_QUERY_RESOURCE_RENDERBUFFER_NV: int
GL_QUERY_RESOURCE_SYS_RESERVED_NV: int
GL_QUERY_RESOURCE_TEXTURE_NV: int
GL_QUERY_RESOURCE_TYPE_VIDMEM_ALLOC_NV: int

def glQueryResourceNV(queryType: int, tagId: int, count: int, buffer: IntArray) -> int: ...

def glInitQueryResourceNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
