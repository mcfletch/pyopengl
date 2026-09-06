"""OpenGL.GL.ARB.framebuffer_no_attachments -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_DEFAULT_FIXED_SAMPLE_LOCATIONS: int
GL_FRAMEBUFFER_DEFAULT_HEIGHT: int
GL_FRAMEBUFFER_DEFAULT_LAYERS: int
GL_FRAMEBUFFER_DEFAULT_SAMPLES: int
GL_FRAMEBUFFER_DEFAULT_WIDTH: int
GL_MAX_FRAMEBUFFER_HEIGHT: int
GL_MAX_FRAMEBUFFER_LAYERS: int
GL_MAX_FRAMEBUFFER_SAMPLES: int
GL_MAX_FRAMEBUFFER_WIDTH: int

def glFramebufferParameteri(target: int, pname: int, param: int) -> None: ...
def glGetFramebufferParameteriv(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...

def glInitFramebufferNoAttachmentsARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
