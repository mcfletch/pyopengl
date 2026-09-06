"""OpenGL.GL.EXT.framebuffer_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_EXT: int
GL_MAX_SAMPLES_EXT: int
GL_RENDERBUFFER_SAMPLES_EXT: int

def glRenderbufferStorageMultisampleEXT(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferMultisampleEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
