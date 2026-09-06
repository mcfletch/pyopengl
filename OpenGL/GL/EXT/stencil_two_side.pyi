"""OpenGL.GL.EXT.stencil_two_side -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ACTIVE_STENCIL_FACE_EXT: int
GL_STENCIL_TEST_TWO_SIDE_EXT: int

def glActiveStencilFaceEXT(face: int) -> None: ...

def glInitStencilTwoSideEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
