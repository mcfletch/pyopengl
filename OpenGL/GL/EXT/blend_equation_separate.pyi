"""OpenGL.GL.EXT.blend_equation_separate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_BLEND_EQUATION_ALPHA_EXT: int
GL_BLEND_EQUATION_RGB_EXT: int

def glBlendEquationSeparateEXT(modeRGB: int, modeAlpha: int) -> None: ...

def glInitBlendEquationSeparateEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
