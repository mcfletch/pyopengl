"""OpenGL.EGL.EXT.device_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array

from OpenGL.raw.EGL._types import *

EGL_BAD_DEVICE_EXT: int
EGL_DEVICE_EXT: int

def eglQueryDeviceAttribEXT(device: Any, attribute: int, value: Int64Array) -> int: ...
def eglQueryDeviceStringEXT(device: Any, name: int) -> bytes: ...
def eglQueryDisplayAttribEXT(dpy: Any, attribute: int, value: Int64Array) -> int: ...

def glInitDeviceQueryEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
