"""OpenGL.EGL.WL.bind_wayland_display -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.EGL._types import *

EGL_TEXTURE_EXTERNAL_WL: int
EGL_TEXTURE_Y_UV_WL: int
EGL_TEXTURE_Y_U_V_WL: int
EGL_TEXTURE_Y_XUXV_WL: int
EGL_WAYLAND_BUFFER_WL: int
EGL_WAYLAND_PLANE_WL: int
EGL_WAYLAND_Y_INVERTED_WL: int

def eglBindWaylandDisplayWL(dpy: Any, display: AnyArray) -> int: ...
def eglQueryWaylandBufferWL(dpy: Any, buffer: AnyArray, attribute: int, value: IntArray) -> int: ...
def eglUnbindWaylandDisplayWL(dpy: Any, display: AnyArray) -> int: ...

def eglInitBindWaylandDisplayWL(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
