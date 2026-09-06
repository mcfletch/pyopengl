"""OpenGL.GLX.SGIX.pbuffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray, UIntArray

from OpenGL.raw.GLX._types import *

GLX_ACCUM_BUFFER_BIT_SGIX: int
GLX_AUX_BUFFERS_BIT_SGIX: int
GLX_BACK_LEFT_BUFFER_BIT_SGIX: int
GLX_BACK_RIGHT_BUFFER_BIT_SGIX: int
GLX_BUFFER_CLOBBER_MASK_SGIX: int
GLX_DAMAGED_SGIX: int
GLX_DEPTH_BUFFER_BIT_SGIX: int
GLX_EVENT_MASK_SGIX: int
GLX_FRONT_LEFT_BUFFER_BIT_SGIX: int
GLX_FRONT_RIGHT_BUFFER_BIT_SGIX: int
GLX_HEIGHT_SGIX: int
GLX_LARGEST_PBUFFER_SGIX: int
GLX_MAX_PBUFFER_HEIGHT_SGIX: int
GLX_MAX_PBUFFER_PIXELS_SGIX: int
GLX_MAX_PBUFFER_WIDTH_SGIX: int
GLX_OPTIMAL_PBUFFER_HEIGHT_SGIX: int
GLX_OPTIMAL_PBUFFER_WIDTH_SGIX: int
GLX_PBUFFER_BIT_SGIX: int
GLX_PBUFFER_SGIX: int
GLX_PRESERVED_CONTENTS_SGIX: int
GLX_SAMPLE_BUFFERS_BIT_SGIX: int
GLX_SAVED_SGIX: int
GLX_STENCIL_BUFFER_BIT_SGIX: int
GLX_WIDTH_SGIX: int
GLX_WINDOW_SGIX: int

def glXCreateGLXPbufferSGIX(dpy: AnyArray, config: Any, width: int, height: int, attrib_list: IntArray) -> Any: ...
def glXDestroyGLXPbufferSGIX(dpy: AnyArray, pbuf: Any) -> None: ...
def glXGetSelectedEventSGIX(dpy: AnyArray, drawable: Any, mask: AnyArray) -> None: ...
def glXQueryGLXPbufferSGIX(dpy: AnyArray, pbuf: Any, attribute: int, value: UIntArray) -> None: ...
def glXSelectEventSGIX(dpy: AnyArray, drawable: Any, mask: int) -> None: ...

def glInitPbufferSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
