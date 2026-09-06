"""OpenGL.EGL.VERSION.EGL_1_2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_ALPHA_FORMAT: int
EGL_ALPHA_FORMAT_NONPRE: int
EGL_ALPHA_FORMAT_PRE: int
EGL_ALPHA_MASK_SIZE: int
EGL_BUFFER_DESTROYED: int
EGL_BUFFER_PRESERVED: int
EGL_CLIENT_APIS: int
EGL_COLORSPACE: int
EGL_COLORSPACE_LINEAR: int
EGL_COLORSPACE_sRGB: int
EGL_COLOR_BUFFER_TYPE: int
EGL_CONTEXT_CLIENT_TYPE: int
EGL_DISPLAY_SCALING: int
EGL_HORIZONTAL_RESOLUTION: int
EGL_LUMINANCE_BUFFER: int
EGL_LUMINANCE_SIZE: int
EGL_OPENGL_ES_API: int
EGL_OPENGL_ES_BIT: int
EGL_OPENVG_API: int
EGL_OPENVG_BIT: int
EGL_OPENVG_IMAGE: int
EGL_PIXEL_ASPECT_RATIO: int
EGL_RENDERABLE_TYPE: int
EGL_RENDER_BUFFER: int
EGL_RGB_BUFFER: int
EGL_SINGLE_BUFFER: int
EGL_SWAP_BEHAVIOR: int
EGL_VERTICAL_RESOLUTION: int

def eglBindAPI(api: int) -> int: ...
def eglCreatePbufferFromClientBuffer(dpy: Any, buftype: int, buffer: Any, config: Any, attrib_list: IntArray) -> Any: ...
def eglQueryAPI() -> int: ...
def eglReleaseThread() -> int: ...
def eglWaitClient() -> int: ...

def glInitEgl12VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
