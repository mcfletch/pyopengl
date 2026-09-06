"""OpenGL.GLX.ARB.create_context -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.GLX._types import *

GLX_CONTEXT_DEBUG_BIT_ARB: int
GLX_CONTEXT_FLAGS_ARB: int
GLX_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB: int
GLX_CONTEXT_MAJOR_VERSION_ARB: int
GLX_CONTEXT_MINOR_VERSION_ARB: int

def glXCreateContextAttribsARB(dpy: AnyArray, config: Any, share_context: Any, direct: int, attrib_list: IntArray) -> Any: ...

def glInitCreateContextARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
