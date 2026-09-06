"""OpenGL.GLES1.APPLE.framebuffer_multisample -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES1._types import *

GL_DRAW_FRAMEBUFFER_APPLE: int
GL_DRAW_FRAMEBUFFER_BINDING_APPLE: int
GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE_APPLE: int
GL_MAX_SAMPLES_APPLE: int
GL_READ_FRAMEBUFFER_APPLE: int
GL_READ_FRAMEBUFFER_BINDING_APPLE: int
GL_RENDERBUFFER_SAMPLES_APPLE: int

def glRenderbufferStorageMultisampleAPPLE(target: int, samples: int, internalformat: int, width: int, height: int) -> None: ...
def glResolveMultisampleFramebufferAPPLE() -> None: ...

def glInitFramebufferMultisampleAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
