"""OpenGL.EGL.KHR.stream -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UInt64Array

from OpenGL.raw.EGL._types import *

EGL_BAD_STATE_KHR: int
EGL_BAD_STREAM_KHR: int
EGL_CONSUMER_FRAME_KHR: int
EGL_CONSUMER_LATENCY_USEC_KHR: int
EGL_PRODUCER_FRAME_KHR: int
EGL_STREAM_STATE_CONNECTING_KHR: int
EGL_STREAM_STATE_CREATED_KHR: int
EGL_STREAM_STATE_DISCONNECTED_KHR: int
EGL_STREAM_STATE_EMPTY_KHR: int
EGL_STREAM_STATE_KHR: int
EGL_STREAM_STATE_NEW_FRAME_AVAILABLE_KHR: int
EGL_STREAM_STATE_OLD_FRAME_AVAILABLE_KHR: int

def eglCreateStreamKHR(dpy: Any, attrib_list: IntArray) -> Any: ...
def eglDestroyStreamKHR(dpy: Any, stream: Any) -> int: ...
def eglQueryStreamKHR(dpy: Any, stream: Any, attribute: int, value: IntArray) -> int: ...
def eglQueryStreamu64KHR(dpy: Any, stream: Any, attribute: int, value: UInt64Array) -> int: ...
def eglStreamAttribKHR(dpy: Any, stream: Any, attribute: int, value: int) -> int: ...

def glInitStreamKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
