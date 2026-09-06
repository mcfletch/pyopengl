"""OpenGL.GLX.MESA.copy_sub_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXCopySubBufferMESA(dpy: AnyArray, drawable: Any, x: int, y: int, width: int, height: int) -> None: ...

def glInitCopySubBufferMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
