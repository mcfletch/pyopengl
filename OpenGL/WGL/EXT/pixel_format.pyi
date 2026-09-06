"""OpenGL.WGL.EXT.pixel_format -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.WGL._types import *

WGL_ACCELERATION_EXT: int
WGL_ACCUM_ALPHA_BITS_EXT: int
WGL_ACCUM_BITS_EXT: int
WGL_ACCUM_BLUE_BITS_EXT: int
WGL_ACCUM_GREEN_BITS_EXT: int
WGL_ACCUM_RED_BITS_EXT: int
WGL_ALPHA_BITS_EXT: int
WGL_ALPHA_SHIFT_EXT: int
WGL_AUX_BUFFERS_EXT: int
WGL_BLUE_BITS_EXT: int
WGL_BLUE_SHIFT_EXT: int
WGL_COLOR_BITS_EXT: int
WGL_DEPTH_BITS_EXT: int
WGL_DOUBLE_BUFFER_EXT: int
WGL_DRAW_TO_BITMAP_EXT: int
WGL_DRAW_TO_WINDOW_EXT: int
WGL_FULL_ACCELERATION_EXT: int
WGL_GENERIC_ACCELERATION_EXT: int
WGL_GREEN_BITS_EXT: int
WGL_GREEN_SHIFT_EXT: int
WGL_NEED_PALETTE_EXT: int
WGL_NEED_SYSTEM_PALETTE_EXT: int
WGL_NO_ACCELERATION_EXT: int
WGL_NUMBER_OVERLAYS_EXT: int
WGL_NUMBER_PIXEL_FORMATS_EXT: int
WGL_NUMBER_UNDERLAYS_EXT: int
WGL_PIXEL_TYPE_EXT: int
WGL_RED_BITS_EXT: int
WGL_RED_SHIFT_EXT: int
WGL_SHARE_ACCUM_EXT: int
WGL_SHARE_DEPTH_EXT: int
WGL_SHARE_STENCIL_EXT: int
WGL_STENCIL_BITS_EXT: int
WGL_STEREO_EXT: int
WGL_SUPPORT_GDI_EXT: int
WGL_SUPPORT_OPENGL_EXT: int
WGL_SWAP_COPY_EXT: int
WGL_SWAP_EXCHANGE_EXT: int
WGL_SWAP_LAYER_BUFFERS_EXT: int
WGL_SWAP_METHOD_EXT: int
WGL_SWAP_UNDEFINED_EXT: int
WGL_TRANSPARENT_EXT: int
WGL_TRANSPARENT_VALUE_EXT: int
WGL_TYPE_COLORINDEX_EXT: int
WGL_TYPE_RGBA_EXT: int

def wglChoosePixelFormatEXT(hdc: Any, piAttribIList: IntArray, pfAttribFList: AnyArray, nMaxFormats: int, piFormats: IntArray, nNumFormats: AnyArray) -> int: ...
def wglGetPixelFormatAttribfvEXT(hdc: Any, iPixelFormat: int, iLayerPlane: int, nAttributes: int, piAttributes: IntArray, pfValues: AnyArray) -> int: ...
def wglGetPixelFormatAttribivEXT(hdc: Any, iPixelFormat: int, iLayerPlane: int, nAttributes: int, piAttributes: IntArray, piValues: IntArray) -> int: ...

def glInitPixelFormatEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
