"""OpenGL.EGL.NV.sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_ALREADY_SIGNALED_NV: int
EGL_CONDITION_SATISFIED_NV: int
EGL_FOREVER_NV: int
EGL_SIGNALED_NV: int
EGL_SYNC_CONDITION_NV: int
EGL_SYNC_FENCE_NV: int
EGL_SYNC_FLUSH_COMMANDS_BIT_NV: int
EGL_SYNC_PRIOR_COMMANDS_COMPLETE_NV: int
EGL_SYNC_STATUS_NV: int
EGL_SYNC_TYPE_NV: int
EGL_TIMEOUT_EXPIRED_NV: int
EGL_UNSIGNALED_NV: int

def eglClientWaitSyncNV(sync: Any, flags: int, timeout: int) -> int: ...
def eglCreateFenceSyncNV(dpy: Any, condition: int, attrib_list: IntArray) -> Any: ...
def eglDestroySyncNV(sync: Any) -> int: ...
def eglFenceNV(sync: Any) -> int: ...
def eglGetSyncAttribNV(sync: Any, attribute: int, value: IntArray) -> int: ...
def eglSignalSyncNV(sync: Any, mode: int) -> int: ...

def glInitSyncNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
