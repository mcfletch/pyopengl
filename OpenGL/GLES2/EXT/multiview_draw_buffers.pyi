"""OpenGL.GLES2.EXT.multiview_draw_buffers -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UIntArray

from OpenGL.raw.GLES2._types import *

GL_COLOR_ATTACHMENT_EXT: int
GL_DRAW_BUFFER_EXT: int
GL_MAX_MULTIVIEW_BUFFERS_EXT: int
GL_MULTIVIEW_EXT: int
GL_READ_BUFFER_EXT: int

def glDrawBuffersIndexedEXT(n: int, location: UIntArray, indices: IntArray) -> None: ...
def glGetIntegeri_vEXT(target: int, index: int, data: IntArray) -> None: ...
def glReadBufferIndexedEXT(src: int, index: int) -> None: ...

def glInitMultiviewDrawBuffersEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
