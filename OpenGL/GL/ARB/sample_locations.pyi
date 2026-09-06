"""OpenGL.GL.ARB.sample_locations -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_PROGRAMMABLE_SAMPLE_LOCATIONS_ARB: int
GL_FRAMEBUFFER_SAMPLE_LOCATION_PIXEL_GRID_ARB: int
GL_PROGRAMMABLE_SAMPLE_LOCATION_ARB: int
GL_PROGRAMMABLE_SAMPLE_LOCATION_TABLE_SIZE_ARB: int
GL_SAMPLE_LOCATION_ARB: int
GL_SAMPLE_LOCATION_PIXEL_GRID_HEIGHT_ARB: int
GL_SAMPLE_LOCATION_PIXEL_GRID_WIDTH_ARB: int
GL_SAMPLE_LOCATION_SUBPIXEL_BITS_ARB: int

def glEvaluateDepthValuesARB() -> None: ...
def glFramebufferSampleLocationsfvARB(target: int, start: int, count: int, v: FloatArray) -> None: ...
def glNamedFramebufferSampleLocationsfvARB(framebuffer: int, start: int, count: int, v: FloatArray) -> None: ...

def glInitSampleLocationsARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
