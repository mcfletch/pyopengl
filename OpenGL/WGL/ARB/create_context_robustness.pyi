"""OpenGL.WGL.ARB.create_context_robustness -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.WGL._types import *

WGL_CONTEXT_RESET_NOTIFICATION_STRATEGY_ARB: int
WGL_CONTEXT_ROBUST_ACCESS_BIT_ARB: int
WGL_LOSE_CONTEXT_ON_RESET_ARB: int
WGL_NO_RESET_NOTIFICATION_ARB: int

def glInitCreateContextRobustnessARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
