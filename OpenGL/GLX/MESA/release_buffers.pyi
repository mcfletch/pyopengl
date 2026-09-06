"""OpenGL.GLX.MESA.release_buffers -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXReleaseBuffersMESA(dpy: AnyArray, drawable: Any) -> int: ...

def glInitReleaseBuffersMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
