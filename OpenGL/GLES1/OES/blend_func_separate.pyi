"""OpenGL.GLES1.OES.blend_func_separate -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES1._types import *

GL_BLEND_DST_ALPHA_OES: int
GL_BLEND_DST_RGB_OES: int
GL_BLEND_SRC_ALPHA_OES: int
GL_BLEND_SRC_RGB_OES: int

def glBlendFuncSeparateOES(srcRGB: int, dstRGB: int, srcAlpha: int, dstAlpha: int) -> None: ...

def glInitBlendFuncSeparateOES() -> bool: ...

def __getattr__(name: str) -> Any: ...
