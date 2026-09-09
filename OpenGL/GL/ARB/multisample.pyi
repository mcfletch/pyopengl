"""OpenGL.GL.ARB.multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_MULTISAMPLE_ARB: int
GL_MULTISAMPLE_BIT_ARB: int
GL_SAMPLES_ARB: int
GL_SAMPLE_ALPHA_TO_COVERAGE_ARB: int
GL_SAMPLE_ALPHA_TO_ONE_ARB: int
GL_SAMPLE_BUFFERS_ARB: int
GL_SAMPLE_COVERAGE_ARB: int
GL_SAMPLE_COVERAGE_INVERT_ARB: int
GL_SAMPLE_COVERAGE_VALUE_ARB: int

def glSampleCoverageARB(value: float, invert: int) -> None: ...

def glInitMultisampleARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
