"""OpenGL.GL.EXT.multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_1PASS_EXT: int
GL_2PASS_0_EXT: int
GL_2PASS_1_EXT: int
GL_4PASS_0_EXT: int
GL_4PASS_1_EXT: int
GL_4PASS_2_EXT: int
GL_4PASS_3_EXT: int
GL_MULTISAMPLE_BIT_EXT: int
GL_MULTISAMPLE_EXT: int
GL_SAMPLES_EXT: int
GL_SAMPLE_ALPHA_TO_MASK_EXT: int
GL_SAMPLE_ALPHA_TO_ONE_EXT: int
GL_SAMPLE_BUFFERS_EXT: int
GL_SAMPLE_MASK_EXT: int
GL_SAMPLE_MASK_INVERT_EXT: int
GL_SAMPLE_MASK_VALUE_EXT: int
GL_SAMPLE_PATTERN_EXT: int

def glSampleMaskEXT(value: float, invert: int) -> None: ...
def glSamplePatternEXT(pattern: int) -> None: ...

def glInitMultisampleEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
