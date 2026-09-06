"""OpenGL.GLX.MESA.query_renderer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, UIntArray

from OpenGL.raw.GLX._types import *

GLX_RENDERER_ACCELERATED_MESA: int
GLX_RENDERER_DEVICE_ID_MESA: int
GLX_RENDERER_OPENGL_COMPATIBILITY_PROFILE_VERSION_MESA: int
GLX_RENDERER_OPENGL_CORE_PROFILE_VERSION_MESA: int
GLX_RENDERER_OPENGL_ES2_PROFILE_VERSION_MESA: int
GLX_RENDERER_OPENGL_ES_PROFILE_VERSION_MESA: int
GLX_RENDERER_PREFERRED_PROFILE_MESA: int
GLX_RENDERER_UNIFIED_MEMORY_ARCHITECTURE_MESA: int
GLX_RENDERER_VENDOR_ID_MESA: int
GLX_RENDERER_VERSION_MESA: int
GLX_RENDERER_VIDEO_MEMORY_MESA: int

def glXQueryCurrentRendererIntegerMESA(attribute: int, value: UIntArray) -> int: ...
def glXQueryCurrentRendererStringMESA(attribute: int) -> bytes: ...
def glXQueryRendererIntegerMESA(dpy: AnyArray, screen: int, renderer: int, attribute: int, value: UIntArray) -> int: ...
def glXQueryRendererStringMESA(dpy: AnyArray, screen: int, renderer: int, attribute: int) -> bytes: ...

def glInitQueryRendererMESA() -> bool: ...

def __getattr__(name: str) -> Any: ...
