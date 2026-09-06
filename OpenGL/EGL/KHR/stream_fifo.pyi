"""OpenGL.EGL.KHR.stream_fifo -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import UInt64Array

from OpenGL.raw.EGL._types import *

EGL_STREAM_FIFO_LENGTH_KHR: int
EGL_STREAM_TIME_CONSUMER_KHR: int
EGL_STREAM_TIME_NOW_KHR: int
EGL_STREAM_TIME_PRODUCER_KHR: int

def eglQueryStreamTimeKHR(dpy: Any, stream: Any, attribute: int, value: UInt64Array) -> int: ...

def glInitStreamFifoKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
