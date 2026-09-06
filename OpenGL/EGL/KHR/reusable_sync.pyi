"""OpenGL.EGL.KHR.reusable_sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_CONDITION_SATISFIED_KHR: int
EGL_FOREVER_KHR: int
EGL_SIGNALED_KHR: int
EGL_SYNC_FLUSH_COMMANDS_BIT_KHR: int
EGL_SYNC_REUSABLE_KHR: int
EGL_SYNC_STATUS_KHR: int
EGL_SYNC_TYPE_KHR: int
EGL_TIMEOUT_EXPIRED_KHR: int
EGL_UNSIGNALED_KHR: int

def eglClientWaitSyncKHR(dpy: Any, sync: Any, flags: int, timeout: int) -> int: ...
def eglCreateSyncKHR(dpy: Any, type: int, attrib_list: IntArray) -> Any: ...
def eglDestroySyncKHR(dpy: Any, sync: Any) -> int: ...
def eglGetSyncAttribKHR(dpy: Any, sync: Any, attribute: int, value: IntArray) -> int: ...
def eglSignalSyncKHR(dpy: Any, sync: Any, mode: int) -> int: ...

def glInitReusableSyncKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
