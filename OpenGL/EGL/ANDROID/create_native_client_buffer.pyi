"""OpenGL.EGL.ANDROID.create_native_client_buffer -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.EGL._types import *

EGL_NATIVE_BUFFER_USAGE_ANDROID: int
EGL_NATIVE_BUFFER_USAGE_PROTECTED_BIT_ANDROID: int
EGL_NATIVE_BUFFER_USAGE_RENDERBUFFER_BIT_ANDROID: int
EGL_NATIVE_BUFFER_USAGE_TEXTURE_BIT_ANDROID: int

def eglCreateNativeClientBufferANDROID(attrib_list: IntArray) -> Any: ...

def eglInitCreateNativeClientBufferANDROID(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
