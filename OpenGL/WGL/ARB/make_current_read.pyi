"""OpenGL.WGL.ARB.make_current_read -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

ERROR_INCOMPATIBLE_DEVICE_CONTEXTS_ARB: int
ERROR_INVALID_PIXEL_TYPE_ARB: int

def wglGetCurrentReadDCARB() -> Any: ...
def wglMakeContextCurrentARB(hDrawDC: Any, hReadDC: Any, hglrc: Any) -> int: ...

def glInitMakeCurrentReadARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
