"""OpenGL.GL.NV.depth_buffer_float -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_DEPTH32F_STENCIL8_NV: int
GL_DEPTH_BUFFER_FLOAT_MODE_NV: int
GL_DEPTH_COMPONENT32F_NV: int
GL_FLOAT_32_UNSIGNED_INT_24_8_REV_NV: int

def glClearDepthdNV(depth: float) -> None: ...
def glDepthBoundsdNV(zmin: float, zmax: float) -> None: ...
def glDepthRangedNV(zNear: float, zFar: float) -> None: ...

def glInitDepthBufferFloatNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
