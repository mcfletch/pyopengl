"""OpenGL.GLES2.EXT.window_rectangles -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.GLES2._types import *

GL_EXCLUSIVE_EXT: int
GL_INCLUSIVE_EXT: int
GL_MAX_WINDOW_RECTANGLES_EXT: int
GL_NUM_WINDOW_RECTANGLES_EXT: int
GL_WINDOW_RECTANGLE_EXT: int
GL_WINDOW_RECTANGLE_MODE_EXT: int

def glWindowRectanglesEXT(mode: int, count: int, box: IntArray) -> None: ...

def glInitWindowRectanglesEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
