"""OpenGL.GL.EXT.stencil_clear_tag -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_STENCIL_CLEAR_TAG_VALUE_EXT: int
GL_STENCIL_TAG_BITS_EXT: int

def glStencilClearTagEXT(stencilTagBits: int, stencilClearTag: int) -> None: ...

def glInitStencilClearTagEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
