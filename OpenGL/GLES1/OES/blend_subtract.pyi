"""OpenGL.GLES1.OES.blend_subtract -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES1._types import *

GL_BLEND_EQUATION_OES: int
GL_FUNC_ADD_OES: int
GL_FUNC_REVERSE_SUBTRACT_OES: int
GL_FUNC_SUBTRACT_OES: int

def glBlendEquationOES(mode: int) -> None: ...

def glInitBlendSubtractOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
