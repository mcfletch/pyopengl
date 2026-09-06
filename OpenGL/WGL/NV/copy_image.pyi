"""OpenGL.WGL.NV.copy_image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

def wglCopyImageSubDataNV(hSrcRC: Any, srcName: int, srcTarget: int, srcLevel: int, srcX: int, srcY: int, srcZ: int, hDstRC: Any, dstName: int, dstTarget: int, dstLevel: int, dstX: int, dstY: int, dstZ: int, width: int, height: int, depth: int) -> int: ...

def glInitCopyImageNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
