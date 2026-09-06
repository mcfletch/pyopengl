"""OpenGL.WGL.ARB.pixel_format -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, IntArray

from OpenGL.raw.WGL._types import *

WGL_ACCELERATION_ARB: int
WGL_ACCUM_ALPHA_BITS_ARB: int
WGL_ACCUM_BITS_ARB: int
WGL_ACCUM_BLUE_BITS_ARB: int
WGL_ACCUM_GREEN_BITS_ARB: int
WGL_ACCUM_RED_BITS_ARB: int
WGL_ALPHA_BITS_ARB: int
WGL_ALPHA_SHIFT_ARB: int
WGL_AUX_BUFFERS_ARB: int
WGL_BLUE_BITS_ARB: int
WGL_BLUE_SHIFT_ARB: int
WGL_COLOR_BITS_ARB: int
WGL_DEPTH_BITS_ARB: int
WGL_DOUBLE_BUFFER_ARB: int
WGL_DRAW_TO_BITMAP_ARB: int
WGL_DRAW_TO_WINDOW_ARB: int
WGL_FULL_ACCELERATION_ARB: int
WGL_GENERIC_ACCELERATION_ARB: int
WGL_GREEN_BITS_ARB: int
WGL_GREEN_SHIFT_ARB: int
WGL_NEED_PALETTE_ARB: int
WGL_NEED_SYSTEM_PALETTE_ARB: int
WGL_NO_ACCELERATION_ARB: int
WGL_NUMBER_OVERLAYS_ARB: int
WGL_NUMBER_PIXEL_FORMATS_ARB: int
WGL_NUMBER_UNDERLAYS_ARB: int
WGL_PIXEL_TYPE_ARB: int
WGL_RED_BITS_ARB: int
WGL_RED_SHIFT_ARB: int
WGL_SHARE_ACCUM_ARB: int
WGL_SHARE_DEPTH_ARB: int
WGL_SHARE_STENCIL_ARB: int
WGL_STENCIL_BITS_ARB: int
WGL_STEREO_ARB: int
WGL_SUPPORT_GDI_ARB: int
WGL_SUPPORT_OPENGL_ARB: int
WGL_SWAP_COPY_ARB: int
WGL_SWAP_EXCHANGE_ARB: int
WGL_SWAP_LAYER_BUFFERS_ARB: int
WGL_SWAP_METHOD_ARB: int
WGL_SWAP_UNDEFINED_ARB: int
WGL_TRANSPARENT_ALPHA_VALUE_ARB: int
WGL_TRANSPARENT_ARB: int
WGL_TRANSPARENT_BLUE_VALUE_ARB: int
WGL_TRANSPARENT_GREEN_VALUE_ARB: int
WGL_TRANSPARENT_INDEX_VALUE_ARB: int
WGL_TRANSPARENT_RED_VALUE_ARB: int
WGL_TYPE_COLORINDEX_ARB: int
WGL_TYPE_RGBA_ARB: int

def wglChoosePixelFormatARB(hdc: Any, piAttribIList: IntArray, pfAttribFList: AnyArray, nMaxFormats: int, piFormats: IntArray, nNumFormats: AnyArray) -> int: ...
def wglGetPixelFormatAttribfvARB(hdc: Any, iPixelFormat: int, iLayerPlane: int, nAttributes: int, piAttributes: IntArray, pfValues: AnyArray) -> int: ...
def wglGetPixelFormatAttribivARB(hdc: Any, iPixelFormat: int, iLayerPlane: int, nAttributes: int, piAttributes: IntArray, piValues: IntArray) -> int: ...

def glInitPixelFormatARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
