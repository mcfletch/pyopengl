"""OpenGL.GL.EXT.raster_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_EFFECTIVE_RASTER_SAMPLES_EXT: int
GL_MAX_RASTER_SAMPLES_EXT: int
GL_MULTISAMPLE_RASTERIZATION_ALLOWED_EXT: int
GL_RASTER_FIXED_SAMPLE_LOCATIONS_EXT: int
GL_RASTER_MULTISAMPLE_EXT: int
GL_RASTER_SAMPLES_EXT: int

def glRasterSamplesEXT(samples: int, fixedsamplelocations: int) -> None: ...

def glInitRasterMultisampleEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
