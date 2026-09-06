"""OpenGL.GLX.SUN.get_transparent_index -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

def glXGetTransparentIndexSUN(dpy: AnyArray, overlay: Any, underlay: Any, pTransparentIndex: AnyArray) -> int: ...

def glInitGetTransparentIndexSUN() -> bool: ...

def __getattr__(name: str) -> Any: ...
