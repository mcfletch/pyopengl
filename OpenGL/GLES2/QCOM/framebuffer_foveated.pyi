"""OpenGL.GLES2.QCOM.framebuffer_foveated -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GLES2._types import *

GL_FOVEATION_ENABLE_BIT_QCOM: int
GL_FOVEATION_SCALED_BIN_METHOD_BIT_QCOM: int

def glFramebufferFoveationConfigQCOM(framebuffer: int, numLayers: int, focalPointsPerLayer: int, requestedFeatures: int, providedFeatures: UIntArray) -> None: ...
def glFramebufferFoveationParametersQCOM(framebuffer: int, layer: int, focalPoint: int, focalX: float, focalY: float, gainX: float, gainY: float, foveaArea: float) -> None: ...

def glInitFramebufferFoveatedQCOM() -> bool: ...

def __getattr__(name: str) -> Any: ...
