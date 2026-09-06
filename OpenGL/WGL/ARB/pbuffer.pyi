"""OpenGL.WGL.ARB.pbuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.WGL._types import *

WGL_DRAW_TO_PBUFFER_ARB: int
WGL_MAX_PBUFFER_HEIGHT_ARB: int
WGL_MAX_PBUFFER_PIXELS_ARB: int
WGL_MAX_PBUFFER_WIDTH_ARB: int
WGL_PBUFFER_HEIGHT_ARB: int
WGL_PBUFFER_LARGEST_ARB: int
WGL_PBUFFER_LOST_ARB: int
WGL_PBUFFER_WIDTH_ARB: int

def wglCreatePbufferARB(hDC: Any, iPixelFormat: int, iWidth: int, iHeight: int, piAttribList: IntArray) -> Any: ...
def wglDestroyPbufferARB(hPbuffer: Any) -> int: ...
def wglGetPbufferDCARB(hPbuffer: Any) -> Any: ...
def wglQueryPbufferARB(hPbuffer: Any, iAttribute: int, piValue: IntArray) -> int: ...
def wglReleasePbufferDCARB(hPbuffer: Any, hDC: Any) -> int: ...

def glInitPbufferARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
