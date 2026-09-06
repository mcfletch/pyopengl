"""OpenGL.GL.AMD.interleaved_elements -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ALPHA: int
GL_BLUE: int
GL_GREEN: int
GL_RED: int
GL_RG16UI: int
GL_RG8UI: int
GL_RGBA8UI: int
GL_VERTEX_ELEMENT_SWIZZLE_AMD: int
GL_VERTEX_ID_SWIZZLE_AMD: int

def glVertexAttribParameteriAMD(index: int, pname: int, param: int) -> None: ...

def glInitInterleavedElementsAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
