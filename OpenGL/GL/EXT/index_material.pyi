"""OpenGL.GL.EXT.index_material -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_INDEX_MATERIAL_EXT: int
GL_INDEX_MATERIAL_FACE_EXT: int
GL_INDEX_MATERIAL_PARAMETER_EXT: int

def glIndexMaterialEXT(face: int, mode: int) -> None: ...

def glInitIndexMaterialEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
