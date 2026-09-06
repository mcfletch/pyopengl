"""OpenGL.GL.EXT.point_parameters -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_DISTANCE_ATTENUATION_EXT: int
GL_POINT_FADE_THRESHOLD_SIZE_EXT: int
GL_POINT_SIZE_MAX_EXT: int
GL_POINT_SIZE_MIN_EXT: int

def glPointParameterfEXT(pname: int, param: float) -> None: ...
def glPointParameterfvEXT(pname: int, params: FloatArray) -> None: ...

def glInitPointParametersEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
