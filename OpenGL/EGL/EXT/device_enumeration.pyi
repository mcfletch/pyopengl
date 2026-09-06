"""OpenGL.EGL.EXT.device_enumeration -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.EGL._types import *

def eglQueryDevicesEXT(max_devices: int, devices: AnyArray, num_devices: IntArray) -> int: ...

def glInitDeviceEnumerationEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
