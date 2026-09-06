"""OpenGL.EGL.KHR.cl_event2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.EGL._types import *

EGL_CL_EVENT_HANDLE_KHR: int
EGL_SYNC_CL_EVENT_COMPLETE_KHR: int
EGL_SYNC_CL_EVENT_KHR: int

def eglCreateSync64KHR(dpy: Any, type: int, attrib_list: AnyArray) -> Any: ...

def glInitClEvent2KHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
