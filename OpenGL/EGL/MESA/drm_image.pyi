"""OpenGL.EGL.MESA.drm_image -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_DRM_BUFFER_FORMAT_ARGB32_MESA: int
EGL_DRM_BUFFER_FORMAT_MESA: int
EGL_DRM_BUFFER_MESA: int
EGL_DRM_BUFFER_STRIDE_MESA: int
EGL_DRM_BUFFER_USE_MESA: int
EGL_DRM_BUFFER_USE_SCANOUT_MESA: int
EGL_DRM_BUFFER_USE_SHARE_MESA: int

def eglCreateDRMImageMESA(dpy: Any, attrib_list: IntArray) -> Any: ...
def eglExportDRMImageMESA(dpy: Any, image: Any, name: IntArray, handle: IntArray, stride: IntArray) -> int: ...

def glInitDrmImageMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
