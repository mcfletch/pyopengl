"""OpenGL.GLX.EXT.texture_from_pixmap -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.GLX._types import *

GLX_AUX0_EXT: int
GLX_AUX1_EXT: int
GLX_AUX2_EXT: int
GLX_AUX3_EXT: int
GLX_AUX4_EXT: int
GLX_AUX5_EXT: int
GLX_AUX6_EXT: int
GLX_AUX7_EXT: int
GLX_AUX8_EXT: int
GLX_AUX9_EXT: int
GLX_BACK_EXT: int
GLX_BACK_LEFT_EXT: int
GLX_BACK_RIGHT_EXT: int
GLX_BIND_TO_MIPMAP_TEXTURE_EXT: int
GLX_BIND_TO_TEXTURE_RGBA_EXT: int
GLX_BIND_TO_TEXTURE_RGB_EXT: int
GLX_BIND_TO_TEXTURE_TARGETS_EXT: int
GLX_FRONT_EXT: int
GLX_FRONT_LEFT_EXT: int
GLX_FRONT_RIGHT_EXT: int
GLX_MIPMAP_TEXTURE_EXT: int
GLX_TEXTURE_1D_BIT_EXT: int
GLX_TEXTURE_1D_EXT: int
GLX_TEXTURE_2D_BIT_EXT: int
GLX_TEXTURE_2D_EXT: int
GLX_TEXTURE_FORMAT_EXT: int
GLX_TEXTURE_FORMAT_NONE_EXT: int
GLX_TEXTURE_FORMAT_RGBA_EXT: int
GLX_TEXTURE_FORMAT_RGB_EXT: int
GLX_TEXTURE_RECTANGLE_BIT_EXT: int
GLX_TEXTURE_RECTANGLE_EXT: int
GLX_TEXTURE_TARGET_EXT: int
GLX_Y_INVERTED_EXT: int

def glXBindTexImageEXT(dpy: AnyArray, drawable: Any, buffer: int, attrib_list: IntArray) -> None: ...
def glXReleaseTexImageEXT(dpy: AnyArray, drawable: Any, buffer: int) -> None: ...

def glInitTextureFromPixmapEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
