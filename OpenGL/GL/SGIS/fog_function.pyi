"""OpenGL.GL.SGIS.fog_function -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult

from OpenGL.raw.GL._types import *

GL_FOG_FUNC_POINTS_SGIS: int
GL_FOG_FUNC_SGIS: int
GL_MAX_FOG_FUNC_POINTS_SGIS: int

def glFogFuncSGIS(n: int, points: FloatArray) -> None: ...
def glGetFogFuncSGIS(points: FloatArray | None = None) -> FloatArrayResult: ...

def glInitFogFunctionSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
