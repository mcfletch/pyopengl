"""OpenGL.EGL.KHR.image_base -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_IMAGE_PRESERVED_KHR: int

def eglCreateImageKHR(dpy: Any, ctx: Any, target: int, buffer: Any, attrib_list: IntArray) -> Any: ...
def eglDestroyImageKHR(dpy: Any, image: Any) -> int: ...

def glInitImageBaseKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
