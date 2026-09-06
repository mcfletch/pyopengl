"""OpenGL.GL.SGIS.multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_1PASS_SGIS: int
GL_2PASS_0_SGIS: int
GL_2PASS_1_SGIS: int
GL_4PASS_0_SGIS: int
GL_4PASS_1_SGIS: int
GL_4PASS_2_SGIS: int
GL_4PASS_3_SGIS: int
GL_MULTISAMPLE_SGIS: int
GL_SAMPLES_SGIS: int
GL_SAMPLE_ALPHA_TO_MASK_SGIS: int
GL_SAMPLE_ALPHA_TO_ONE_SGIS: int
GL_SAMPLE_BUFFERS_SGIS: int
GL_SAMPLE_MASK_INVERT_SGIS: int
GL_SAMPLE_MASK_SGIS: int
GL_SAMPLE_MASK_VALUE_SGIS: int
GL_SAMPLE_PATTERN_SGIS: int

def glSampleMaskSGIS(value: float, invert: bool) -> None: ...
def glSamplePatternSGIS(pattern: int) -> None: ...

def glInitMultisampleSGIS() -> bool: ...

def __getattr__(name: str) -> Any: ...
