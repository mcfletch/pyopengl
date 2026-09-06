"""OpenGL.WGL.NV.video_output -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.WGL._types import *

WGL_BIND_TO_VIDEO_RGBA_NV: int
WGL_BIND_TO_VIDEO_RGB_AND_DEPTH_NV: int
WGL_BIND_TO_VIDEO_RGB_NV: int
WGL_VIDEO_OUT_ALPHA_NV: int
WGL_VIDEO_OUT_COLOR_AND_ALPHA_NV: int
WGL_VIDEO_OUT_COLOR_AND_DEPTH_NV: int
WGL_VIDEO_OUT_COLOR_NV: int
WGL_VIDEO_OUT_DEPTH_NV: int
WGL_VIDEO_OUT_FIELD_1: int
WGL_VIDEO_OUT_FIELD_2: int
WGL_VIDEO_OUT_FRAME: int
WGL_VIDEO_OUT_STACKED_FIELDS_1_2: int
WGL_VIDEO_OUT_STACKED_FIELDS_2_1: int

def wglBindVideoImageNV(hVideoDevice: Any, hPbuffer: Any, iVideoBuffer: int) -> int: ...
def wglGetVideoDeviceNV(hDC: Any, numDevices: int, hVideoDevice: AnyArray) -> int: ...
def wglGetVideoInfoNV(hpVideoDevice: Any, pulCounterOutputPbuffer: AnyArray, pulCounterOutputVideo: AnyArray) -> int: ...
def wglReleaseVideoDeviceNV(hVideoDevice: Any) -> int: ...
def wglReleaseVideoImageNV(hPbuffer: Any, iVideoBuffer: int) -> int: ...
def wglSendPbufferToVideoNV(hPbuffer: Any, iBufferType: int, pulCounterPbuffer: AnyArray, bBlock: int) -> int: ...

def glInitVideoOutputNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
