"""OpenGL.GL.SUN.mesh_array -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_QUAD_MESH_SUN: int
GL_TRIANGLE_MESH_SUN: int

def glDrawMeshArraysSUN(mode: int, first: int, count: int, width: int) -> None: ...

def glInitMeshArraySUN() -> bool: ...

def __getattr__(name: str) -> Any: ...
