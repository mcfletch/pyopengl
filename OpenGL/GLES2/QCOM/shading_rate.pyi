"""OpenGL.GLES2.QCOM.shading_rate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_SHADING_RATE_1X1_PIXELS_QCOM: int
GL_SHADING_RATE_1X2_PIXELS_QCOM: int
GL_SHADING_RATE_2X1_PIXELS_QCOM: int
GL_SHADING_RATE_2X2_PIXELS_QCOM: int
GL_SHADING_RATE_4X2_PIXELS_QCOM: int
GL_SHADING_RATE_4X4_PIXELS_QCOM: int
GL_SHADING_RATE_PRESERVE_ASPECT_RATIO_QCOM: int
GL_SHADING_RATE_QCOM: int

def glShadingRateQCOM(rate: int) -> None: ...

def glInitShadingRateQCOM() -> bool: ...

def __getattr__(name: str) -> Any: ...
