"""OpenGL.WGL.I3D.digital_video_control -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.WGL._types import *

WGL_DIGITAL_VIDEO_CURSOR_ALPHA_FRAMEBUFFER_I3D: int
WGL_DIGITAL_VIDEO_CURSOR_ALPHA_VALUE_I3D: int
WGL_DIGITAL_VIDEO_CURSOR_INCLUDED_I3D: int
WGL_DIGITAL_VIDEO_GAMMA_CORRECTED_I3D: int

def wglGetDigitalVideoParametersI3D(hDC: Any, iAttribute: int, piValue: IntArray) -> int: ...
def wglSetDigitalVideoParametersI3D(hDC: Any, iAttribute: int, piValue: IntArray) -> int: ...

def glInitDigitalVideoControlI3D() -> bool: ...

def __getattr__(name: str) -> Any: ...
