"""OpenGL.GLES2.QCOM.motion_estimation -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FOVEATION_SCALED_BIN_METHOD_BIT_QCOM: int
GL_MOTION_ESTIMATION_SEARCH_BLOCK_X_QCOM: int
GL_MOTION_ESTIMATION_SEARCH_BLOCK_Y_QCOM: int

def glTexEstimateMotionQCOM(ref: int, target: int, output: int) -> None: ...
def glTexEstimateMotionRegionsQCOM(ref: int, target: int, output: int, mask: int) -> None: ...

def glInitMotionEstimationQCOM() -> bool: ...

def __getattr__(name: str) -> Any: ...
