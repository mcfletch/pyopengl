"""OpenGL.GLES2.NV.framebuffer_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_NV: int
GL_MAX_SAMPLES_NV: int
GL_RENDERBUFFER_SAMPLES_NV: int

def glRenderbufferStorageMultisampleNV(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferMultisampleNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
