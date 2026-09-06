"""OpenGL.GLES2.APPLE.copy_texture_levels -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

def glCopyTextureLevelsAPPLE(destinationTexture: int, sourceTexture: int, sourceBaseLevel: int, sourceLevelCount: int) -> None: ...

def glInitCopyTextureLevelsAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
