"""OpenGL.GL.EXT.index_func -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_INDEX_TEST_EXT: int
GL_INDEX_TEST_FUNC_EXT: int
GL_INDEX_TEST_REF_EXT: int

def glIndexFuncEXT(func: int, ref: float) -> None: ...

def glInitIndexFuncEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
