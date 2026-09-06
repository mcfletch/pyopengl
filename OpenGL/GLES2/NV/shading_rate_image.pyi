"""OpenGL.GLES2.NV.shading_rate_image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UIntArray

from OpenGL.raw.GLES2._types import *

GL_MAX_COARSE_FRAGMENT_SAMPLES_NV: int
GL_SHADING_RATE_16_INVOCATIONS_PER_PIXEL_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_1X2_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_2X1_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_2X2_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_2X4_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_4X2_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_4X4_PIXELS_NV: int
GL_SHADING_RATE_1_INVOCATION_PER_PIXEL_NV: int
GL_SHADING_RATE_2_INVOCATIONS_PER_PIXEL_NV: int
GL_SHADING_RATE_4_INVOCATIONS_PER_PIXEL_NV: int
GL_SHADING_RATE_8_INVOCATIONS_PER_PIXEL_NV: int
GL_SHADING_RATE_IMAGE_BINDING_NV: int
GL_SHADING_RATE_IMAGE_NV: int
GL_SHADING_RATE_IMAGE_PALETTE_SIZE_NV: int
GL_SHADING_RATE_IMAGE_TEXEL_HEIGHT_NV: int
GL_SHADING_RATE_IMAGE_TEXEL_WIDTH_NV: int
GL_SHADING_RATE_NO_INVOCATIONS_NV: int
GL_SHADING_RATE_SAMPLE_ORDER_DEFAULT_NV: int
GL_SHADING_RATE_SAMPLE_ORDER_PIXEL_MAJOR_NV: int
GL_SHADING_RATE_SAMPLE_ORDER_SAMPLE_MAJOR_NV: int

def glBindShadingRateImageNV(texture: int) -> None: ...
def glGetShadingRateImagePaletteNV(viewport: int, entry: int, rate: UIntArray) -> None: ...
def glGetShadingRateSampleLocationivNV(rate: int, samples: int, index: int, location: IntArray) -> None: ...
def glShadingRateImageBarrierNV(synchronize: bool) -> None: ...
def glShadingRateImagePaletteNV(viewport: int, first: int, count: int, rates: UIntArray) -> None: ...
def glShadingRateSampleOrderCustomNV(rate: int, samples: int, locations: IntArray) -> None: ...
def glShadingRateSampleOrderNV(order: int) -> None: ...

def glInitShadingRateImageNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
