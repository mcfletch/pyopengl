"""OpenGL.GL.AMD.framebuffer_sample_positions -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray

from OpenGL.raw.GL._types import *

GL_ALL_PIXELS_AMD: int
GL_PIXELS_PER_SAMPLE_PATTERN_X_AMD: int
GL_PIXELS_PER_SAMPLE_PATTERN_Y_AMD: int
GL_SUBSAMPLE_DISTANCE_AMD: int

def glFramebufferSamplePositionsfvAMD(target: int, numsamples: int, pixelindex: int, values: FloatArray) -> None: ...
def glGetFramebufferParameterfvAMD(target: int, pname: int, numsamples: int, pixelindex: int, size: int, values: FloatArray) -> None: ...
def glGetNamedFramebufferParameterfvAMD(framebuffer: int, pname: int, numsamples: int, pixelindex: int, size: int, values: FloatArray) -> None: ...
def glNamedFramebufferSamplePositionsfvAMD(framebuffer: int, numsamples: int, pixelindex: int, values: FloatArray) -> None: ...

def glInitFramebufferSamplePositionsAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
