"""OpenGL.EGL.KHR.stream_producer_eglsurface -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_STREAM_BIT_KHR: int

def eglCreateStreamProducerSurfaceKHR(dpy: Any, config: Any, stream: Any, attrib_list: IntArray) -> Any: ...

def glInitStreamProducerEglsurfaceKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
