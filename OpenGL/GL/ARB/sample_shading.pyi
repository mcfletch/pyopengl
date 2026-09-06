"""OpenGL.GL.ARB.sample_shading -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MIN_SAMPLE_SHADING_VALUE_ARB: int
GL_SAMPLE_SHADING_ARB: int

def glMinSampleShadingARB(value: float) -> None: ...

def glInitSampleShadingARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
