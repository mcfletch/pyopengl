"""OpenGL.WGL.ARB.context_flush_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

WGL_CONTEXT_RELEASE_BEHAVIOR_ARB: int
WGL_CONTEXT_RELEASE_BEHAVIOR_FLUSH_ARB: int
WGL_CONTEXT_RELEASE_BEHAVIOR_NONE_ARB: int

def glInitContextFlushControlARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
