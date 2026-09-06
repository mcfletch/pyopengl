"""OpenGL.GL.SGIS.detail_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_DETAIL_TEXTURE_2D_BINDING_SGIS: int
GL_DETAIL_TEXTURE_2D_SGIS: int
GL_DETAIL_TEXTURE_FUNC_POINTS_SGIS: int
GL_DETAIL_TEXTURE_LEVEL_SGIS: int
GL_DETAIL_TEXTURE_MODE_SGIS: int
GL_LINEAR_DETAIL_ALPHA_SGIS: int
GL_LINEAR_DETAIL_COLOR_SGIS: int
GL_LINEAR_DETAIL_SGIS: int

def glDetailTexFuncSGIS(target: int, n: int, points: FloatArray) -> None: ...
def glGetDetailTexFuncSGIS(target: int, points: FloatArray | None = None) -> FloatArrayResult: ...

def glInitDetailTextureSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
