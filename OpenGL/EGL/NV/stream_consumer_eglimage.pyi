"""OpenGL.EGL.NV.stream_consumer_eglimage -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, Int64Array, UInt64Array

from OpenGL.raw.EGL._types import *

EGL_STREAM_CONSUMER_IMAGE_NV: int
EGL_STREAM_IMAGE_ADD_NV: int
EGL_STREAM_IMAGE_AVAILABLE_NV: int
EGL_STREAM_IMAGE_REMOVE_NV: int

def eglQueryStreamConsumerEventNV(dpy: Any, stream: Any, timeout: int, event: AnyArray, aux: Int64Array) -> int: ...
def eglStreamAcquireImageNV(dpy: Any, stream: Any, pImage: AnyArray, sync: Any) -> int: ...
def eglStreamImageConsumerConnectNV(dpy: Any, stream: Any, num_modifiers: int, modifiers: UInt64Array, attrib_list: Int64Array) -> int: ...
def eglStreamReleaseImageNV(dpy: Any, stream: Any, image: Any, sync: Any) -> int: ...

def eglInitStreamConsumerEglimageNV(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
