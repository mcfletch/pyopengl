"""OpenGL.WGL.ARB.create_context -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.WGL._types import *

ERROR_INVALID_VERSION_ARB: int
WGL_CONTEXT_DEBUG_BIT_ARB: int
WGL_CONTEXT_FLAGS_ARB: int
WGL_CONTEXT_FORWARD_COMPATIBLE_BIT_ARB: int
WGL_CONTEXT_LAYER_PLANE_ARB: int
WGL_CONTEXT_MAJOR_VERSION_ARB: int
WGL_CONTEXT_MINOR_VERSION_ARB: int

def wglCreateContextAttribsARB(hDC: Any, hShareContext: Any, attribList: IntArray) -> Any: ...

def glInitCreateContextARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
