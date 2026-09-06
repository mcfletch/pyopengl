"""OpenGL.GL.NV.fragment_coverage_to_color -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAGMENT_COVERAGE_COLOR_NV: int
GL_FRAGMENT_COVERAGE_TO_COLOR_NV: int

def glFragmentCoverageColorNV(color: int) -> None: ...

def glInitFragmentCoverageToColorNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
