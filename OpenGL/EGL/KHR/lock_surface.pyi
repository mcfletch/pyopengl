"""OpenGL.EGL.KHR.lock_surface -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_BITMAP_ORIGIN_KHR: int
EGL_BITMAP_PITCH_KHR: int
EGL_BITMAP_PIXEL_ALPHA_OFFSET_KHR: int
EGL_BITMAP_PIXEL_BLUE_OFFSET_KHR: int
EGL_BITMAP_PIXEL_GREEN_OFFSET_KHR: int
EGL_BITMAP_PIXEL_LUMINANCE_OFFSET_KHR: int
EGL_BITMAP_PIXEL_RED_OFFSET_KHR: int
EGL_BITMAP_POINTER_KHR: int
EGL_FORMAT_RGBA_8888_EXACT_KHR: int
EGL_FORMAT_RGBA_8888_KHR: int
EGL_FORMAT_RGB_565_EXACT_KHR: int
EGL_FORMAT_RGB_565_KHR: int
EGL_LOCK_SURFACE_BIT_KHR: int
EGL_LOCK_USAGE_HINT_KHR: int
EGL_LOWER_LEFT_KHR: int
EGL_MAP_PRESERVE_PIXELS_KHR: int
EGL_MATCH_FORMAT_KHR: int
EGL_OPTIMAL_FORMAT_BIT_KHR: int
EGL_READ_SURFACE_BIT_KHR: int
EGL_UPPER_LEFT_KHR: int
EGL_WRITE_SURFACE_BIT_KHR: int

def eglLockSurfaceKHR(dpy: Any, surface: Any, attrib_list: IntArray) -> int: ...
def eglUnlockSurfaceKHR(dpy: Any, surface: Any) -> int: ...

def glInitLockSurfaceKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
