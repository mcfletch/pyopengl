"""OpenGL.EGL.VERSION.EGL_1_0 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, IntArray

from OpenGL.raw.EGL._types import *

EGL_ALPHA_SIZE: int
EGL_BAD_ACCESS: int
EGL_BAD_ALLOC: int
EGL_BAD_ATTRIBUTE: int
EGL_BAD_CONFIG: int
EGL_BAD_CONTEXT: int
EGL_BAD_CURRENT_SURFACE: int
EGL_BAD_DISPLAY: int
EGL_BAD_MATCH: int
EGL_BAD_NATIVE_PIXMAP: int
EGL_BAD_NATIVE_WINDOW: int
EGL_BAD_PARAMETER: int
EGL_BAD_SURFACE: int
EGL_BLUE_SIZE: int
EGL_BUFFER_SIZE: int
EGL_CONFIG_CAVEAT: int
EGL_CONFIG_ID: int
EGL_CORE_NATIVE_ENGINE: int
EGL_DEPTH_SIZE: int
EGL_DRAW: int
EGL_EXTENSIONS: int
EGL_FALSE: int
EGL_GREEN_SIZE: int
EGL_HEIGHT: int
EGL_LARGEST_PBUFFER: int
EGL_LEVEL: int
EGL_MAX_PBUFFER_HEIGHT: int
EGL_MAX_PBUFFER_PIXELS: int
EGL_MAX_PBUFFER_WIDTH: int
EGL_NATIVE_RENDERABLE: int
EGL_NATIVE_VISUAL_ID: int
EGL_NATIVE_VISUAL_TYPE: int
EGL_NONE: int
EGL_NON_CONFORMANT_CONFIG: int
EGL_NOT_INITIALIZED: int
EGL_PBUFFER_BIT: int
EGL_PIXMAP_BIT: int
EGL_READ: int
EGL_RED_SIZE: int
EGL_SAMPLES: int
EGL_SAMPLE_BUFFERS: int
EGL_SLOW_CONFIG: int
EGL_STENCIL_SIZE: int
EGL_SUCCESS: int
EGL_SURFACE_TYPE: int
EGL_TRANSPARENT_BLUE_VALUE: int
EGL_TRANSPARENT_GREEN_VALUE: int
EGL_TRANSPARENT_RED_VALUE: int
EGL_TRANSPARENT_RGB: int
EGL_TRANSPARENT_TYPE: int
EGL_TRUE: int
EGL_VENDOR: int
EGL_VERSION: int
EGL_WIDTH: int
EGL_WINDOW_BIT: int

def eglChooseConfig(dpy: Any, attrib_list: IntArray, configs: AnyArray, config_size: int, num_config: IntArray) -> int: ...
def eglCopyBuffers(dpy: Any, surface: Any, target: Any) -> int: ...
def eglCreateContext(dpy: Any, config: Any, share_context: Any, attrib_list: IntArray) -> Any: ...
def eglCreatePbufferSurface(dpy: Any, config: Any, attrib_list: IntArray) -> Any: ...
def eglCreatePixmapSurface(dpy: Any, config: Any, pixmap: Any, attrib_list: IntArray) -> Any: ...
def eglCreateWindowSurface(dpy: Any, config: Any, win: Any, attrib_list: IntArray) -> Any: ...
def eglDestroyContext(dpy: Any, ctx: Any) -> int: ...
def eglDestroySurface(dpy: Any, surface: Any) -> int: ...
def eglGetConfigAttrib(dpy: Any, config: Any, attribute: int, value: IntArray) -> int: ...
def eglGetConfigs(dpy: Any, configs: AnyArray, config_size: int, num_config: IntArray) -> int: ...
def eglGetCurrentDisplay() -> Any: ...
def eglGetCurrentSurface(readdraw: int) -> Any: ...
def eglGetDisplay(display_id: Any) -> Any: ...
def eglGetError() -> int: ...
def eglGetProcAddress(procname: ByteArray) -> int | None: ...
def eglInitialize(dpy: Any, major: IntArray, minor: IntArray) -> int: ...
def eglMakeCurrent(dpy: Any, draw: Any, read: Any, ctx: Any) -> int: ...
def eglQueryContext(dpy: Any, ctx: Any, attribute: int, value: IntArray) -> int: ...
def eglQueryString(dpy: Any, name: int) -> bytes: ...
def eglQuerySurface(dpy: Any, surface: Any, attribute: int, value: IntArray) -> int: ...
def eglSwapBuffers(dpy: Any, surface: Any) -> int: ...
def eglTerminate(dpy: Any) -> int: ...
def eglWaitGL() -> int: ...
def eglWaitNative(engine: int) -> int: ...

def glInitEgl10VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
