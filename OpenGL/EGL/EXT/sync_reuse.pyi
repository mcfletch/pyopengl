"""OpenGL.EGL.EXT.sync_reuse -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array

from OpenGL.raw.EGL._types import *

def eglUnsignalSyncEXT(dpy: Any, sync: Any, attrib_list: Int64Array) -> int: ...

def eglInitSyncReuseEXT(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
