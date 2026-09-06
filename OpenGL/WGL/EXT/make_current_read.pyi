"""OpenGL.WGL.EXT.make_current_read -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

ERROR_INVALID_PIXEL_TYPE_EXT: int

def wglGetCurrentReadDCEXT() -> Any: ...
def wglMakeContextCurrentEXT(hDrawDC: Any, hReadDC: Any, hglrc: Any) -> int: ...

def glInitMakeCurrentReadEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
