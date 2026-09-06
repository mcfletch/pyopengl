"""OpenGL.GL.EXT.depth_bounds_test -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_DEPTH_BOUNDS_EXT: int
GL_DEPTH_BOUNDS_TEST_EXT: int

def glDepthBoundsEXT(zmin: float, zmax: float) -> None: ...

def glInitDepthBoundsTestEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
