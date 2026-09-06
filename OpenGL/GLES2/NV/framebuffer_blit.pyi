"""OpenGL.GLES2.NV.framebuffer_blit -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_DRAW_FRAMEBUFFER_BINDING_NV: int
GL_DRAW_FRAMEBUFFER_NV: int
GL_READ_FRAMEBUFFER_BINDING_NV: int
GL_READ_FRAMEBUFFER_NV: int

def glBlitFramebufferNV(srcX0: int, srcY0: int, srcX1: int, srcY1: int, dstX0: int, dstY0: int, dstX1: int, dstY1: int, mask: int, filter: int) -> None: ...

def glInitFramebufferBlitNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
