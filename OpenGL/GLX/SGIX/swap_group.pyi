"""OpenGL.GLX.SGIX.swap_group -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXJoinSwapGroupSGIX(dpy: AnyArray, drawable: Any, member: Any) -> None: ...

def glInitSwapGroupSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
