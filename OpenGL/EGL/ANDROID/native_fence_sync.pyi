"""OpenGL.EGL.ANDROID.native_fence_sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_NO_NATIVE_FENCE_FD_ANDROID: int
EGL_SYNC_NATIVE_FENCE_ANDROID: int
EGL_SYNC_NATIVE_FENCE_FD_ANDROID: int
EGL_SYNC_NATIVE_FENCE_SIGNALED_ANDROID: int

def eglDupNativeFenceFDANDROID(dpy: Any, sync: Any) -> int: ...

def glInitNativeFenceSyncANDROID() -> bool: ...

def __getattr__(name: str) -> Any: ...
