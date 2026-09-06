"""OpenGL.GL.NV.copy_image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GL._types import *

def glCopyImageSubDataNV(srcName: int, srcTarget: int, srcLevel: int, srcX: int, srcY: int, srcZ: int, dstName: int, dstTarget: int, dstLevel: int, dstX: int, dstY: int, dstZ: int, width: int, height: int, depth: int) -> None: ...

def glInitCopyImageNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
