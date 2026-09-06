"""OpenGL.GLES2.EXT.shader_pixel_local_storage2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UIntArray

from OpenGL.raw.GLES2._types import *

GL_FRAMEBUFFER_INCOMPLETE_INSUFFICIENT_SHADER_COMBINED_LOCAL_STORAGE_EXT: int
GL_MAX_SHADER_COMBINED_LOCAL_STORAGE_FAST_SIZE_EXT: int
GL_MAX_SHADER_COMBINED_LOCAL_STORAGE_SIZE_EXT: int

def glClearPixelLocalStorageuiEXT(offset: int, n: int, values: UIntArray) -> None: ...
def glFramebufferPixelLocalStorageSizeEXT(target: int, size: int) -> None: ...
def glGetFramebufferPixelLocalStorageSizeEXT(target: int) -> int: ...

def glInitShaderPixelLocalStorage2EXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
