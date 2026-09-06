"""OpenGL.GL.EXT.draw_range_elements -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_MAX_ELEMENTS_INDICES_EXT: int
GL_MAX_ELEMENTS_VERTICES_EXT: int

def glDrawRangeElementsEXT(mode: int, start: int, end: int, count: int, type: int, indices: AnyArray) -> None: ...

def glInitDrawRangeElementsEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
