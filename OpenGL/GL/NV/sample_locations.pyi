"""OpenGL.GL.NV.sample_locations -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_PROGRAMMABLE_SAMPLE_LOCATIONS_NV: int
GL_FRAMEBUFFER_SAMPLE_LOCATION_PIXEL_GRID_NV: int
GL_PROGRAMMABLE_SAMPLE_LOCATION_NV: int
GL_PROGRAMMABLE_SAMPLE_LOCATION_TABLE_SIZE_NV: int
GL_SAMPLE_LOCATION_NV: int
GL_SAMPLE_LOCATION_PIXEL_GRID_HEIGHT_NV: int
GL_SAMPLE_LOCATION_PIXEL_GRID_WIDTH_NV: int
GL_SAMPLE_LOCATION_SUBPIXEL_BITS_NV: int

def glFramebufferSampleLocationsfvNV(target: int, start: int, count: int, v: FloatArray) -> None: ...
def glNamedFramebufferSampleLocationsfvNV(framebuffer: int, start: int, count: int, v: FloatArray) -> None: ...
def glResolveDepthValuesNV() -> None: ...

def glInitSampleLocationsNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
