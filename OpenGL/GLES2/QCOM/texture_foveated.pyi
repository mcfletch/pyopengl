"""OpenGL.GLES2.QCOM.texture_foveated -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FOVEATION_ENABLE_BIT_QCOM: int
GL_FOVEATION_SCALED_BIN_METHOD_BIT_QCOM: int
GL_FRAMEBUFFER_INCOMPLETE_FOVEATION_QCOM: int
GL_TEXTURE_FOVEATED_FEATURE_BITS_QCOM: int
GL_TEXTURE_FOVEATED_FEATURE_QUERY_QCOM: int
GL_TEXTURE_FOVEATED_MIN_PIXEL_DENSITY_QCOM: int
GL_TEXTURE_FOVEATED_NUM_FOCAL_POINTS_QUERY_QCOM: int

def glTextureFoveationParametersQCOM(texture: int, layer: int, focalPoint: int, focalX: float, focalY: float, gainX: float, gainY: float, foveaArea: float) -> None: ...

def glInitTextureFoveatedQCOM() -> bool: ...

def __getattr__(name: str) -> Any: ...
