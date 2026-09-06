"""OpenGL.EGL.NV.stream_reset -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_SUPPORT_RESET_NV: int
EGL_SUPPORT_REUSE_NV: int

def eglResetStreamNV(dpy: Any, stream: Any) -> int: ...

def eglInitStreamResetNV(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
