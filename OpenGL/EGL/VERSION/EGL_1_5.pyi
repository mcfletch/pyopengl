"""OpenGL.EGL.VERSION.EGL_1_5 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, Int64Array

from OpenGL.raw.EGL._types import *

EGL_CL_EVENT_HANDLE: int
EGL_CONDITION_SATISFIED: int
EGL_CONTEXT_MAJOR_VERSION: int
EGL_CONTEXT_MINOR_VERSION: int
EGL_CONTEXT_OPENGL_COMPATIBILITY_PROFILE_BIT: int
EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT: int
EGL_CONTEXT_OPENGL_DEBUG: int
EGL_CONTEXT_OPENGL_FORWARD_COMPATIBLE: int
EGL_CONTEXT_OPENGL_PROFILE_MASK: int
EGL_CONTEXT_OPENGL_RESET_NOTIFICATION_STRATEGY: int
EGL_CONTEXT_OPENGL_ROBUST_ACCESS: int
EGL_FOREVER: int
EGL_GL_COLORSPACE: int
EGL_GL_COLORSPACE_LINEAR: int
EGL_GL_COLORSPACE_SRGB: int
EGL_GL_RENDERBUFFER: int
EGL_GL_TEXTURE_2D: int
EGL_GL_TEXTURE_3D: int
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_X: int
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: int
EGL_GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: int
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_X: int
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Y: int
EGL_GL_TEXTURE_CUBE_MAP_POSITIVE_Z: int
EGL_GL_TEXTURE_LEVEL: int
EGL_GL_TEXTURE_ZOFFSET: int
EGL_IMAGE_PRESERVED: int
EGL_LOSE_CONTEXT_ON_RESET: int
EGL_NO_RESET_NOTIFICATION: int
EGL_OPENGL_ES3_BIT: int
EGL_SIGNALED: int
EGL_SYNC_CL_EVENT: int
EGL_SYNC_CL_EVENT_COMPLETE: int
EGL_SYNC_CONDITION: int
EGL_SYNC_FENCE: int
EGL_SYNC_FLUSH_COMMANDS_BIT: int
EGL_SYNC_PRIOR_COMMANDS_COMPLETE: int
EGL_SYNC_STATUS: int
EGL_SYNC_TYPE: int
EGL_TIMEOUT_EXPIRED: int
EGL_UNSIGNALED: int

def eglClientWaitSync(dpy: Any, sync: Any, flags: int, timeout: int) -> int: ...
def eglCreateImage(dpy: Any, ctx: Any, target: int, buffer: Any, attrib_list: Int64Array) -> Any: ...
def eglCreatePlatformPixmapSurface(dpy: Any, config: Any, native_pixmap: AnyArray, attrib_list: Int64Array) -> Any: ...
def eglCreatePlatformWindowSurface(dpy: Any, config: Any, native_window: AnyArray, attrib_list: Int64Array) -> Any: ...
def eglCreateSync(dpy: Any, type: int, attrib_list: Int64Array) -> Any: ...
def eglDestroyImage(dpy: Any, image: Any) -> int: ...
def eglDestroySync(dpy: Any, sync: Any) -> int: ...
def eglGetPlatformDisplay(platform: int, native_display: AnyArray, attrib_list: Int64Array) -> Any: ...
def eglGetSyncAttrib(dpy: Any, sync: Any, attribute: int, value: Int64Array) -> int: ...
def eglWaitSync(dpy: Any, sync: Any, flags: int) -> int: ...

def glInitEgl15VERSION() -> bool: ...

def __getattr__(name: str) -> Any: ...
