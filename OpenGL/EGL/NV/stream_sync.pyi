"""OpenGL.EGL.NV.stream_sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_SYNC_NEW_FRAME_NV: int
EGL_SYNC_TYPE_KHR: int

def eglCreateStreamSyncNV(dpy: Any, stream: Any, type: int, attrib_list: IntArray) -> Any: ...

def glInitStreamSyncNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
