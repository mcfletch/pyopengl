"""OpenGL.GL.SGIS.sharpen_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_LINEAR_SHARPEN_ALPHA_SGIS: int
GL_LINEAR_SHARPEN_COLOR_SGIS: int
GL_LINEAR_SHARPEN_SGIS: int
GL_SHARPEN_TEXTURE_FUNC_POINTS_SGIS: int

def glGetSharpenTexFuncSGIS(target: int, points: FloatArray | None = None) -> FloatArrayResult: ...
def glSharpenTexFuncSGIS(target: int, n: int, points: FloatArray) -> None: ...

def glInitSharpenTextureSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
