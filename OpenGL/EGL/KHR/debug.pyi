"""OpenGL.EGL.KHR.debug -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array

from OpenGL.raw.EGL._types import *

EGL_DEBUG_CALLBACK_KHR: int
EGL_DEBUG_MSG_CRITICAL_KHR: int
EGL_DEBUG_MSG_ERROR_KHR: int
EGL_DEBUG_MSG_INFO_KHR: int
EGL_DEBUG_MSG_WARN_KHR: int
EGL_OBJECT_CONTEXT_KHR: int
EGL_OBJECT_DISPLAY_KHR: int
EGL_OBJECT_IMAGE_KHR: int
EGL_OBJECT_STREAM_KHR: int
EGL_OBJECT_SURFACE_KHR: int
EGL_OBJECT_SYNC_KHR: int
EGL_OBJECT_THREAD_KHR: int

def eglDebugMessageControlKHR(callback: Any, attrib_list: Int64Array) -> int: ...
def eglLabelObjectKHR(display: Any, objectType: int, object: Any, label: Any) -> int: ...
def eglQueryDebugKHR(attribute: int, value: Int64Array) -> int: ...

def glInitDebugKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
