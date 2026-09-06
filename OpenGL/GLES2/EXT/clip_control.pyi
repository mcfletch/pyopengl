"""OpenGL.GLES2.EXT.clip_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_CLIP_DEPTH_MODE_EXT: int
GL_CLIP_ORIGIN_EXT: int
GL_LOWER_LEFT_EXT: int
GL_NEGATIVE_ONE_TO_ONE_EXT: int
GL_UPPER_LEFT_EXT: int
GL_ZERO_TO_ONE_EXT: int

def glClipControlEXT(origin: int, depth: int) -> None: ...

def glInitClipControlEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
