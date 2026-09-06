"""OpenGL.GLES1.OES.blend_equation_separate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES1._types import *

GL_BLEND_EQUATION_ALPHA_OES: int
GL_BLEND_EQUATION_RGB_OES: int

def glBlendEquationSeparateOES(modeRGB: int, modeAlpha: int) -> None: ...

def glInitBlendEquationSeparateOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
