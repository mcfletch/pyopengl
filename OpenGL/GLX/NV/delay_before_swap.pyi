"""OpenGL.GLX.NV.delay_before_swap -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXDelayBeforeSwapNV(dpy: AnyArray, drawable: Any, seconds: float) -> int: ...

def glInitDelayBeforeSwapNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
