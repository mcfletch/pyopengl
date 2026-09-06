"""OpenGL.GL.INTEL.parallel_arrays -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_COLOR_ARRAY_PARALLEL_POINTERS_INTEL: int
GL_NORMAL_ARRAY_PARALLEL_POINTERS_INTEL: int
GL_PARALLEL_ARRAYS_INTEL: int
GL_TEXTURE_COORD_ARRAY_PARALLEL_POINTERS_INTEL: int
GL_VERTEX_ARRAY_PARALLEL_POINTERS_INTEL: int

def glColorPointervINTEL(size: int, type: int, pointer: AnyArray) -> None: ...
def glNormalPointervINTEL(type: int, pointer: AnyArray) -> None: ...
def glTexCoordPointervINTEL(size: int, type: int, pointer: AnyArray) -> None: ...
def glVertexPointervINTEL(size: int, type: int, pointer: AnyArray) -> None: ...

def glInitParallelArraysINTEL() -> bool: ...

def __getattr__(name: str) -> Any: ...
