"""OpenGL.EGL.KHR.image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_NATIVE_PIXMAP_KHR: int

def eglCreateImageKHR(dpy: Any, ctx: Any, target: int, buffer: Any, attrib_list: IntArray) -> Any: ...
def eglDestroyImageKHR(dpy: Any, image: Any) -> int: ...

def glInitImageKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
