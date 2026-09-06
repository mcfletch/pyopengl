"""OpenGL.GL.INTEL.map_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UIntArray

from OpenGL.raw.GL._types import *

GL_LAYOUT_DEFAULT_INTEL: int
GL_LAYOUT_LINEAR_CPU_CACHED_INTEL: int
GL_LAYOUT_LINEAR_INTEL: int
GL_TEXTURE_MEMORY_LAYOUT_INTEL: int

def glMapTexture2DINTEL(texture: int, level: int, access: int, stride: IntArray, layout: UIntArray) -> int | None: ...
def glSyncTextureINTEL(texture: int) -> None: ...
def glUnmapTexture2DINTEL(texture: int, level: int) -> None: ...

def glInitMapTextureINTEL() -> bool: ...

def __getattr__(name: str) -> Any: ...
