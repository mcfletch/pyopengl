"""OpenGL.GLX.EXT.swap_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

GLX_MAX_SWAP_INTERVAL_EXT: int
GLX_SWAP_INTERVAL_EXT: int

def glXSwapIntervalEXT(dpy: AnyArray, drawable: Any, interval: int) -> None: ...

def glInitSwapControlEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
