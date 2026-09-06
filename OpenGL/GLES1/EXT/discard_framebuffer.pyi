"""OpenGL.GLES1.EXT.discard_framebuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GLES1._types import *

GL_COLOR_EXT: int
GL_DEPTH_EXT: int
GL_STENCIL_EXT: int

def glDiscardFramebufferEXT(target: int, numAttachments: int, attachments: UIntArray) -> None: ...

def glInitDiscardFramebufferEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
