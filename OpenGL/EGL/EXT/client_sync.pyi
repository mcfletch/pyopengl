"""OpenGL.EGL.EXT.client_sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array

from OpenGL.raw.EGL._types import *

EGL_SYNC_CLIENT_EXT: int
EGL_SYNC_CLIENT_SIGNAL_EXT: int

def eglClientSignalSyncEXT(dpy: Any, sync: Any, attrib_list: Int64Array) -> int: ...

def eglInitClientSyncEXT(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
