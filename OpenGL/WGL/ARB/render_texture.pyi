"""OpenGL.WGL.ARB.render_texture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray

from OpenGL.raw.WGL._types import *

WGL_AUX0_ARB: int
WGL_AUX1_ARB: int
WGL_AUX2_ARB: int
WGL_AUX3_ARB: int
WGL_AUX4_ARB: int
WGL_AUX5_ARB: int
WGL_AUX6_ARB: int
WGL_AUX7_ARB: int
WGL_AUX8_ARB: int
WGL_AUX9_ARB: int
WGL_BACK_LEFT_ARB: int
WGL_BACK_RIGHT_ARB: int
WGL_BIND_TO_TEXTURE_RGBA_ARB: int
WGL_BIND_TO_TEXTURE_RGB_ARB: int
WGL_CUBE_MAP_FACE_ARB: int
WGL_FRONT_LEFT_ARB: int
WGL_FRONT_RIGHT_ARB: int
WGL_MIPMAP_LEVEL_ARB: int
WGL_MIPMAP_TEXTURE_ARB: int
WGL_NO_TEXTURE_ARB: int
WGL_TEXTURE_1D_ARB: int
WGL_TEXTURE_2D_ARB: int
WGL_TEXTURE_CUBE_MAP_ARB: int
WGL_TEXTURE_CUBE_MAP_NEGATIVE_X_ARB: int
WGL_TEXTURE_CUBE_MAP_NEGATIVE_Y_ARB: int
WGL_TEXTURE_CUBE_MAP_NEGATIVE_Z_ARB: int
WGL_TEXTURE_CUBE_MAP_POSITIVE_X_ARB: int
WGL_TEXTURE_CUBE_MAP_POSITIVE_Y_ARB: int
WGL_TEXTURE_CUBE_MAP_POSITIVE_Z_ARB: int
WGL_TEXTURE_FORMAT_ARB: int
WGL_TEXTURE_RGBA_ARB: int
WGL_TEXTURE_RGB_ARB: int
WGL_TEXTURE_TARGET_ARB: int

def wglBindTexImageARB(hPbuffer: Any, iBuffer: int) -> int: ...
def wglReleaseTexImageARB(hPbuffer: Any, iBuffer: int) -> int: ...
def wglSetPbufferAttribARB(hPbuffer: Any, piAttribList: IntArray) -> int: ...

def glInitRenderTextureARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
