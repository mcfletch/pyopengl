"""OpenGL.GL.EXT.framebuffer_blit -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_DRAW_FRAMEBUFFER_BINDING_EXT: int
GL_DRAW_FRAMEBUFFER_EXT: int
GL_READ_FRAMEBUFFER_BINDING_EXT: int
GL_READ_FRAMEBUFFER_EXT: int

def glBlitFramebufferEXT(srcX0: int, srcY0: int, srcX1: int, srcY1: int, dstX0: int, dstY0: int, dstX1: int, dstY1: int, mask: int, filter: int) -> None: ...

def glInitFramebufferBlitEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
