"""OpenGL.GLES2.EXT.copy_image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

def glCopyImageSubDataEXT(srcName: int, srcTarget: int, srcLevel: int, srcX: int, srcY: int, srcZ: int, dstName: int, dstTarget: int, dstLevel: int, dstX: int, dstY: int, dstZ: int, srcWidth: int, srcHeight: int, srcDepth: int) -> None: ...

def glInitCopyImageEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
