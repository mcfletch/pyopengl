"""OpenGL.GLES2.ANGLE.framebuffer_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_ANGLE: int
GL_MAX_SAMPLES_ANGLE: int
GL_RENDERBUFFER_SAMPLES_ANGLE: int

def glRenderbufferStorageMultisampleANGLE(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...

def glInitFramebufferMultisampleANGLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
