"""OpenGL.EGL.VERSION.EGL_1_1 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.EGL._types import *

EGL_BACK_BUFFER: int
EGL_BIND_TO_TEXTURE_RGB: int
EGL_BIND_TO_TEXTURE_RGBA: int
EGL_CONTEXT_LOST: int
EGL_MAX_SWAP_INTERVAL: int
EGL_MIN_SWAP_INTERVAL: int
EGL_MIPMAP_LEVEL: int
EGL_MIPMAP_TEXTURE: int
EGL_NO_TEXTURE: int
EGL_TEXTURE_2D: int
EGL_TEXTURE_FORMAT: int
EGL_TEXTURE_RGB: int
EGL_TEXTURE_RGBA: int
EGL_TEXTURE_TARGET: int

def eglBindTexImage(dpy: Any, surface: Any, buffer: int) -> int: ...
def eglReleaseTexImage(dpy: Any, surface: Any, buffer: int) -> int: ...
def eglSurfaceAttrib(dpy: Any, surface: Any, attribute: int, value: int) -> int: ...
def eglSwapInterval(dpy: Any, interval: int) -> int: ...

def glInitEgl11VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
