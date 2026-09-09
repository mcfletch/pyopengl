"""OpenGL.GLX.NV.video_out -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GLX._types import *

GLX_VIDEO_OUT_ALPHA_NV: int
GLX_VIDEO_OUT_COLOR_AND_ALPHA_NV: int
GLX_VIDEO_OUT_COLOR_AND_DEPTH_NV: int
GLX_VIDEO_OUT_COLOR_NV: int
GLX_VIDEO_OUT_DEPTH_NV: int
GLX_VIDEO_OUT_FIELD_1_NV: int
GLX_VIDEO_OUT_FIELD_2_NV: int
GLX_VIDEO_OUT_FRAME_NV: int
GLX_VIDEO_OUT_STACKED_FIELDS_1_2_NV: int
GLX_VIDEO_OUT_STACKED_FIELDS_2_1_NV: int

def glXBindVideoImageNV(dpy: AnyArray, VideoDevice: Any, pbuf: Any, iVideoBuffer: int) -> int: ...
def glXGetVideoDeviceNV(dpy: AnyArray, screen: int, numVideoDevices: int, pVideoDevice: AnyArray) -> int: ...
def glXGetVideoInfoNV(dpy: AnyArray, screen: int, VideoDevice: Any, pulCounterOutputPbuffer: AnyArray, pulCounterOutputVideo: AnyArray) -> int: ...
def glXReleaseVideoDeviceNV(dpy: AnyArray, screen: int, VideoDevice: Any) -> int: ...
def glXReleaseVideoImageNV(dpy: AnyArray, pbuf: Any) -> int: ...
def glXSendPbufferToVideoNV(dpy: AnyArray, pbuf: Any, iBufferType: int, pulCounterPbuffer: AnyArray, bBlock: int) -> int: ...

def glInitVideoOutNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
