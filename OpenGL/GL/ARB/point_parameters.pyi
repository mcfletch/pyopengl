"""OpenGL.GL.ARB.point_parameters -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_POINT_DISTANCE_ATTENUATION_ARB: int
GL_POINT_FADE_THRESHOLD_SIZE_ARB: int
GL_POINT_SIZE_MAX_ARB: int
GL_POINT_SIZE_MIN_ARB: int

def glPointParameterfARB(pname: int, param: float) -> None: ...
def glPointParameterfvARB(pname: int, params: FloatArray) -> None: ...

def glInitPointParametersARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
