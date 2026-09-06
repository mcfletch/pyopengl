"""OpenGL.GL.NV.clip_space_w_scaling -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_VIEWPORT_POSITION_W_SCALE_NV: int
GL_VIEWPORT_POSITION_W_SCALE_X_COEFF_NV: int
GL_VIEWPORT_POSITION_W_SCALE_Y_COEFF_NV: int

def glViewportPositionWScaleNV(index: int, xcoeff: float, ycoeff: float) -> None: ...

def glInitClipSpaceWScalingNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
