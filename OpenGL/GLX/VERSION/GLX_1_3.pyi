"""OpenGL.GLX.VERSION.GLX_1_3 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray, UIntArray

from OpenGL.raw.GLX._types import *

GLX_ACCUM_BUFFER_BIT: int
GLX_AUX_BUFFERS_BIT: int
GLX_BACK_LEFT_BUFFER_BIT: int
GLX_BACK_RIGHT_BUFFER_BIT: int
GLX_COLOR_INDEX_BIT: int
GLX_COLOR_INDEX_TYPE: int
GLX_CONFIG_CAVEAT: int
GLX_DAMAGED: int
GLX_DEPTH_BUFFER_BIT: int
GLX_DIRECT_COLOR: int
GLX_DONT_CARE: int
GLX_DRAWABLE_TYPE: int
GLX_EVENT_MASK: int
GLX_FBCONFIG_ID: int
GLX_FRONT_LEFT_BUFFER_BIT: int
GLX_FRONT_RIGHT_BUFFER_BIT: int
GLX_GRAY_SCALE: int
GLX_HEIGHT: int
GLX_LARGEST_PBUFFER: int
GLX_MAX_PBUFFER_HEIGHT: int
GLX_MAX_PBUFFER_PIXELS: int
GLX_MAX_PBUFFER_WIDTH: int
GLX_NONE: int
GLX_NON_CONFORMANT_CONFIG: int
GLX_PBUFFER: int
GLX_PBUFFER_BIT: int
GLX_PBUFFER_CLOBBER_MASK: int
GLX_PBUFFER_HEIGHT: int
GLX_PBUFFER_WIDTH: int
GLX_PIXMAP_BIT: int
GLX_PRESERVED_CONTENTS: int
GLX_PSEUDO_COLOR: int
GLX_RENDER_TYPE: int
GLX_RGBA_BIT: int
GLX_RGBA_TYPE: int
GLX_SAVED: int
GLX_SCREEN: int
GLX_SLOW_CONFIG: int
GLX_STATIC_COLOR: int
GLX_STATIC_GRAY: int
GLX_STENCIL_BUFFER_BIT: int
GLX_TRANSPARENT_ALPHA_VALUE: int
GLX_TRANSPARENT_BLUE_VALUE: int
GLX_TRANSPARENT_GREEN_VALUE: int
GLX_TRANSPARENT_INDEX: int
GLX_TRANSPARENT_INDEX_VALUE: int
GLX_TRANSPARENT_RED_VALUE: int
GLX_TRANSPARENT_RGB: int
GLX_TRANSPARENT_TYPE: int
GLX_TRUE_COLOR: int
GLX_VISUAL_ID: int
GLX_WIDTH: int
GLX_WINDOW: int
GLX_WINDOW_BIT: int
GLX_X_RENDERABLE: int
GLX_X_VISUAL_TYPE: int

def glXChooseFBConfig(dpy: AnyArray, screen: int, attrib_list: IntArray, nelements: IntArray) -> bytes: ...
def glXCreateNewContext(dpy: AnyArray, config: Any, render_type: int, share_list: Any, direct: int) -> Any: ...
def glXCreatePbuffer(dpy: AnyArray, config: Any, attrib_list: IntArray) -> Any: ...
def glXCreatePixmap(dpy: AnyArray, config: Any, pixmap: Any, attrib_list: IntArray) -> Any: ...
def glXCreateWindow(dpy: AnyArray, config: Any, win: Any, attrib_list: IntArray) -> Any: ...
def glXDestroyPbuffer(dpy: AnyArray, pbuf: Any) -> None: ...
def glXDestroyPixmap(dpy: AnyArray, pixmap: Any) -> None: ...
def glXDestroyWindow(dpy: AnyArray, win: Any) -> None: ...
def glXGetCurrentReadDrawable() -> Any: ...
def glXGetFBConfigAttrib(dpy: AnyArray, config: Any, attribute: int, value: IntArray) -> int: ...
def glXGetFBConfigs(dpy: AnyArray, screen: int, nelements: IntArray) -> bytes: ...
def glXGetSelectedEvent(dpy: AnyArray, draw: Any, event_mask: AnyArray) -> None: ...
def glXGetVisualFromFBConfig(dpy: AnyArray, config: Any) -> bytes: ...
def glXMakeContextCurrent(dpy: AnyArray, draw: Any, read: Any, ctx: Any) -> int: ...
def glXQueryContext(dpy: AnyArray, ctx: Any, attribute: int, value: IntArray) -> int: ...
def glXQueryDrawable(dpy: AnyArray, draw: Any, attribute: int, value: UIntArray) -> None: ...
def glXSelectEvent(dpy: AnyArray, draw: Any, event_mask: int) -> None: ...

def glInitGlx13VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
