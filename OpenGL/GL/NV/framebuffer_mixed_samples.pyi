"""OpenGL.GL.NV.framebuffer_mixed_samples -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_COLOR_SAMPLES_NV: int
GL_COVERAGE_MODULATION_NV: int
GL_COVERAGE_MODULATION_TABLE_NV: int
GL_COVERAGE_MODULATION_TABLE_SIZE_NV: int
GL_DEPTH_SAMPLES_NV: int
GL_EFFECTIVE_RASTER_SAMPLES_EXT: int
GL_MAX_RASTER_SAMPLES_EXT: int
GL_MIXED_DEPTH_SAMPLES_SUPPORTED_NV: int
GL_MIXED_STENCIL_SAMPLES_SUPPORTED_NV: int
GL_MULTISAMPLE_RASTERIZATION_ALLOWED_EXT: int
GL_RASTER_FIXED_SAMPLE_LOCATIONS_EXT: int
GL_RASTER_MULTISAMPLE_EXT: int
GL_RASTER_SAMPLES_EXT: int
GL_STENCIL_SAMPLES_NV: int

def glCoverageModulationNV(components: int) -> None: ...
def glCoverageModulationTableNV(n: int, v: FloatArray) -> None: ...
def glGetCoverageModulationTableNV(bufSize: int, v: FloatArray) -> None: ...
def glRasterSamplesEXT(samples: int, fixedsamplelocations: bool) -> None: ...

def glInitFramebufferMixedSamplesNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
