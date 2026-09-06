"""OpenGL.GL.SGIS.point_parameters -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_DISTANCE_ATTENUATION_SGIS: int
GL_POINT_FADE_THRESHOLD_SIZE_SGIS: int
GL_POINT_SIZE_MAX_SGIS: int
GL_POINT_SIZE_MIN_SGIS: int

def glPointParameterfSGIS(pname: int, param: float) -> None: ...
def glPointParameterfvSGIS(pname: int, params: FloatArray) -> None: ...

def glInitPointParametersSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
