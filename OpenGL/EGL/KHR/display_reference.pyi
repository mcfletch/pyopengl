"""OpenGL.EGL.KHR.display_reference -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array

from OpenGL.raw.EGL._types import *

EGL_TRACK_REFERENCES_KHR: int

def eglQueryDisplayAttribKHR(dpy: Any, name: int, value: Int64Array) -> int: ...

def eglInitDisplayReferenceKHR(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
