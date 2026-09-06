"""OpenGL.GLX.SGIX.fbconfig -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.GLX._types import *

GLX_COLOR_INDEX_BIT_SGIX: int
GLX_COLOR_INDEX_TYPE_SGIX: int
GLX_DRAWABLE_TYPE_SGIX: int
GLX_FBCONFIG_ID_SGIX: int
GLX_PIXMAP_BIT_SGIX: int
GLX_RENDER_TYPE_SGIX: int
GLX_RGBA_BIT_SGIX: int
GLX_RGBA_TYPE_SGIX: int
GLX_SCREEN_EXT: int
GLX_WINDOW_BIT_SGIX: int
GLX_X_RENDERABLE_SGIX: int

def glXChooseFBConfigSGIX(dpy: AnyArray, screen: int, attrib_list: IntArray, nelements: IntArray) -> bytes: ...
def glXCreateContextWithConfigSGIX(dpy: AnyArray, config: Any, render_type: int, share_list: Any, direct: int) -> Any: ...
def glXCreateGLXPixmapWithConfigSGIX(dpy: AnyArray, config: Any, pixmap: Any) -> Any: ...
def glXGetFBConfigAttribSGIX(dpy: AnyArray, config: Any, attribute: int, value: IntArray) -> int: ...
def glXGetFBConfigFromVisualSGIX(dpy: AnyArray, vis: AnyArray) -> Any: ...
def glXGetVisualFromFBConfigSGIX(dpy: AnyArray, config: Any) -> bytes: ...

def glInitFbconfigSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
