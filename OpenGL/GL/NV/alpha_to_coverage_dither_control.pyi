"""OpenGL.GL.NV.alpha_to_coverage_dither_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_ALPHA_TO_COVERAGE_DITHER_DEFAULT_NV: int
GL_ALPHA_TO_COVERAGE_DITHER_DISABLE_NV: int
GL_ALPHA_TO_COVERAGE_DITHER_ENABLE_NV: int
GL_ALPHA_TO_COVERAGE_DITHER_MODE_NV: int

def glAlphaToCoverageDitherControlNV(mode: int) -> None: ...

def glInitAlphaToCoverageDitherControlNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
