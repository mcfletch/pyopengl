"""OpenGL.GLES2.EXT.draw_buffers_indexed -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_BLEND: int
GL_BLEND_DST_ALPHA: int
GL_BLEND_DST_RGB: int
GL_BLEND_EQUATION_ALPHA: int
GL_BLEND_EQUATION_RGB: int
GL_BLEND_SRC_ALPHA: int
GL_BLEND_SRC_RGB: int
GL_COLOR_WRITEMASK: int
GL_CONSTANT_ALPHA: int
GL_CONSTANT_COLOR: int
GL_DST_ALPHA: int
GL_DST_COLOR: int
GL_FUNC_ADD: int
GL_FUNC_REVERSE_SUBTRACT: int
GL_FUNC_SUBTRACT: int
GL_MAX: int
GL_MIN: int
GL_ONE: int
GL_ONE_MINUS_CONSTANT_ALPHA: int
GL_ONE_MINUS_CONSTANT_COLOR: int
GL_ONE_MINUS_DST_ALPHA: int
GL_ONE_MINUS_DST_COLOR: int
GL_ONE_MINUS_SRC_ALPHA: int
GL_ONE_MINUS_SRC_COLOR: int
GL_SRC_ALPHA: int
GL_SRC_ALPHA_SATURATE: int
GL_SRC_COLOR: int
GL_ZERO: int

def glBlendEquationSeparateiEXT(buf: int, modeRGB: int, modeAlpha: int) -> None: ...
def glBlendEquationiEXT(buf: int, mode: int) -> None: ...
def glBlendFuncSeparateiEXT(buf: int, srcRGB: int, dstRGB: int, srcAlpha: int, dstAlpha: int) -> None: ...
def glBlendFunciEXT(buf: int, src: int, dst: int) -> None: ...
def glColorMaskiEXT(index: int, r: int, g: int, b: int, a: int) -> None: ...
def glDisableiEXT(target: int, index: int) -> None: ...
def glEnableiEXT(target: int, index: int) -> None: ...
def glIsEnablediEXT(target: int, index: int) -> int: ...

def glInitDrawBuffersIndexedEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
