"""OpenGL.EGL.KHR.wait_sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

def eglWaitSyncKHR(dpy: Any, sync: Any, flags: int) -> int: ...

def glInitWaitSyncKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
