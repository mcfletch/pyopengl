"""OpenGL.GL.VERSION.GL_1_2 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray

from OpenGL.raw.GL._types import *

GL_ALIASED_LINE_WIDTH_RANGE: int
GL_ALIASED_POINT_SIZE_RANGE: int
GL_BGR: int
GL_BGRA: int
GL_CLAMP_TO_EDGE: int
GL_LIGHT_MODEL_COLOR_CONTROL: int
GL_MAX_3D_TEXTURE_SIZE: int
GL_MAX_ELEMENTS_INDICES: int
GL_MAX_ELEMENTS_VERTICES: int
GL_PACK_IMAGE_HEIGHT: int
GL_PACK_SKIP_IMAGES: int
GL_PROXY_TEXTURE_3D: int
GL_RESCALE_NORMAL: int
GL_SEPARATE_SPECULAR_COLOR: int
GL_SINGLE_COLOR: int
GL_SMOOTH_LINE_WIDTH_GRANULARITY: int
GL_SMOOTH_LINE_WIDTH_RANGE: int
GL_SMOOTH_POINT_SIZE_GRANULARITY: int
GL_SMOOTH_POINT_SIZE_RANGE: int
GL_TEXTURE_3D: int
GL_TEXTURE_BASE_LEVEL: int
GL_TEXTURE_BINDING_3D: int
GL_TEXTURE_DEPTH: int
GL_TEXTURE_MAX_LEVEL: int
GL_TEXTURE_MAX_LOD: int
GL_TEXTURE_MIN_LOD: int
GL_TEXTURE_WRAP_R: int
GL_UNPACK_IMAGE_HEIGHT: int
GL_UNPACK_SKIP_IMAGES: int
GL_UNSIGNED_BYTE_2_3_3_REV: int
GL_UNSIGNED_BYTE_3_3_2: int
GL_UNSIGNED_INT_10_10_10_2: int
GL_UNSIGNED_INT_2_10_10_10_REV: int
GL_UNSIGNED_INT_8_8_8_8: int
GL_UNSIGNED_INT_8_8_8_8_REV: int
GL_UNSIGNED_SHORT_1_5_5_5_REV: int
GL_UNSIGNED_SHORT_4_4_4_4: int
GL_UNSIGNED_SHORT_4_4_4_4_REV: int
GL_UNSIGNED_SHORT_5_5_5_1: int
GL_UNSIGNED_SHORT_5_6_5: int
GL_UNSIGNED_SHORT_5_6_5_REV: int

def glCopyTexSubImage3D(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, x: int, y: int, width: int, height: int) -> None: ...
def glDrawRangeElements(mode: int, start: int, end: int, count: int, type: int, indices: AnyArray) -> None: ...
def glTexImage3D(target: int, level: int, internalformat: int, width: int, height: int, depth: int, border: int, format: int, type: int, pixels: AnyArray) -> None: ...
def glTexSubImage3D(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, type: int, pixels: AnyArray) -> None: ...

def glInitGl12VERSION() -> bool: ...
GL_POINT_SIZE_GRANULARITY: int
GL_POINT_SIZE_RANGE: int
GL_LINE_WIDTH_GRANULARITY: int
GL_LINE_WIDTH_RANGE: int

def __getattr__(name: str) -> Any: ...
