"""OpenGL.WGL.EXT.pbuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.WGL._types import *

WGL_DRAW_TO_PBUFFER_EXT: int
WGL_MAX_PBUFFER_HEIGHT_EXT: int
WGL_MAX_PBUFFER_PIXELS_EXT: int
WGL_MAX_PBUFFER_WIDTH_EXT: int
WGL_OPTIMAL_PBUFFER_HEIGHT_EXT: int
WGL_OPTIMAL_PBUFFER_WIDTH_EXT: int
WGL_PBUFFER_HEIGHT_EXT: int
WGL_PBUFFER_LARGEST_EXT: int
WGL_PBUFFER_WIDTH_EXT: int

def wglCreatePbufferEXT(hDC: Any, iPixelFormat: int, iWidth: int, iHeight: int, piAttribList: IntArray) -> Any: ...
def wglDestroyPbufferEXT(hPbuffer: Any) -> int: ...
def wglGetPbufferDCEXT(hPbuffer: Any) -> Any: ...
def wglQueryPbufferEXT(hPbuffer: Any, iAttribute: int, piValue: IntArray) -> int: ...
def wglReleasePbufferDCEXT(hPbuffer: Any, hDC: Any) -> int: ...

def glInitPbufferEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
