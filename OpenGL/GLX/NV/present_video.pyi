"""OpenGL.GLX.NV.present_video -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.GLX._types import *

GLX_NUM_VIDEO_SLOTS_NV: int

def glXBindVideoDeviceNV(dpy: AnyArray, video_slot: int, video_device: int, attrib_list: IntArray) -> int: ...
def glXEnumerateVideoDevicesNV(dpy: AnyArray, screen: int, nelements: IntArray) -> bytes: ...

def glInitPresentVideoNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
