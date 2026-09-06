"""OpenGL.EGL.EXT.device_persistent_id -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.EGL._types import *

EGL_DEVICE_UUID_EXT: int
EGL_DRIVER_NAME_EXT: int
EGL_DRIVER_UUID_EXT: int

def eglQueryDeviceBinaryEXT(device: Any, name: int, max_size: int, value: AnyArray, size: IntArray) -> int: ...

def eglInitDevicePersistentIdEXT(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
