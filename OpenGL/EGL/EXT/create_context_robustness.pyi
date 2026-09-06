"""OpenGL.EGL.EXT.create_context_robustness -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY_EXT: int
EGL_CONTEXT_OPENGL_ROBUST_ACCESS_EXT: int
EGL_LOSE_CONTEXT_ON_RESET_EXT: int
EGL_NO_RESET_NOTIFICATION_EXT: int

def glInitCreateContextRobustnessEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
