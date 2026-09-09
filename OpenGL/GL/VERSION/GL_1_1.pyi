"""OpenGL.GL.VERSION.GL_1_1 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, FloatArray, UByteArray, UByteArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *
from OpenGL.GL.VERSION.GL_1_0 import *

GL_ALPHA12: int
GL_ALPHA16: int
GL_ALPHA4: int
GL_ALPHA8: int
GL_C3F_V3F: int
GL_C4F_N3F_V3F: int
GL_C4UB_V2F: int
GL_C4UB_V3F: int
GL_CLIENT_ALL_ATTRIB_BITS: int
GL_CLIENT_ATTRIB_STACK_DEPTH: int
GL_CLIENT_PIXEL_STORE_BIT: int
GL_CLIENT_VERTEX_ARRAY_BIT: int
GL_COLOR_ARRAY: int
GL_COLOR_ARRAY_POINTER: int
GL_COLOR_ARRAY_SIZE: int
GL_COLOR_ARRAY_STRIDE: int
GL_COLOR_ARRAY_TYPE: int
GL_COLOR_LOGIC_OP: int
GL_EDGE_FLAG_ARRAY: int
GL_EDGE_FLAG_ARRAY_POINTER: int
GL_EDGE_FLAG_ARRAY_STRIDE: int
GL_FEEDBACK_BUFFER_POINTER: int
GL_FEEDBACK_BUFFER_SIZE: int
GL_FEEDBACK_BUFFER_TYPE: int
GL_INDEX_ARRAY: int
GL_INDEX_ARRAY_POINTER: int
GL_INDEX_ARRAY_STRIDE: int
GL_INDEX_ARRAY_TYPE: int
GL_INDEX_LOGIC_OP: int
GL_INTENSITY: int
GL_INTENSITY12: int
GL_INTENSITY16: int
GL_INTENSITY4: int
GL_INTENSITY8: int
GL_LUMINANCE12: int
GL_LUMINANCE12_ALPHA12: int
GL_LUMINANCE12_ALPHA4: int
GL_LUMINANCE16: int
GL_LUMINANCE16_ALPHA16: int
GL_LUMINANCE4: int
GL_LUMINANCE4_ALPHA4: int
GL_LUMINANCE6_ALPHA2: int
GL_LUMINANCE8: int
GL_LUMINANCE8_ALPHA8: int
GL_MAX_CLIENT_ATTRIB_STACK_DEPTH: int
GL_N3F_V3F: int
GL_NORMAL_ARRAY: int
GL_NORMAL_ARRAY_POINTER: int
GL_NORMAL_ARRAY_STRIDE: int
GL_NORMAL_ARRAY_TYPE: int
GL_POLYGON_OFFSET_FACTOR: int
GL_POLYGON_OFFSET_FILL: int
GL_POLYGON_OFFSET_LINE: int
GL_POLYGON_OFFSET_POINT: int
GL_POLYGON_OFFSET_UNITS: int
GL_PROXY_TEXTURE_1D: int
GL_PROXY_TEXTURE_2D: int
GL_R3_G3_B2: int
GL_RGB10: int
GL_RGB10_A2: int
GL_RGB12: int
GL_RGB16: int
GL_RGB4: int
GL_RGB5: int
GL_RGB5_A1: int
GL_RGB8: int
GL_RGBA12: int
GL_RGBA16: int
GL_RGBA2: int
GL_RGBA4: int
GL_RGBA8: int
GL_SELECTION_BUFFER_POINTER: int
GL_SELECTION_BUFFER_SIZE: int
GL_T2F_C3F_V3F: int
GL_T2F_C4F_N3F_V3F: int
GL_T2F_C4UB_V3F: int
GL_T2F_N3F_V3F: int
GL_T2F_V3F: int
GL_T4F_C4F_N3F_V4F: int
GL_T4F_V4F: int
GL_TEXTURE_ALPHA_SIZE: int
GL_TEXTURE_BINDING_1D: int
GL_TEXTURE_BINDING_2D: int
GL_TEXTURE_BLUE_SIZE: int
GL_TEXTURE_COORD_ARRAY: int
GL_TEXTURE_COORD_ARRAY_POINTER: int
GL_TEXTURE_COORD_ARRAY_SIZE: int
GL_TEXTURE_COORD_ARRAY_STRIDE: int
GL_TEXTURE_COORD_ARRAY_TYPE: int
GL_TEXTURE_GREEN_SIZE: int
GL_TEXTURE_INTENSITY_SIZE: int
GL_TEXTURE_INTERNAL_FORMAT: int
GL_TEXTURE_LUMINANCE_SIZE: int
GL_TEXTURE_PRIORITY: int
GL_TEXTURE_RED_SIZE: int
GL_TEXTURE_RESIDENT: int
GL_V2F: int
GL_V3F: int
GL_VERTEX_ARRAY: int
GL_VERTEX_ARRAY_POINTER: int
GL_VERTEX_ARRAY_SIZE: int
GL_VERTEX_ARRAY_STRIDE: int
GL_VERTEX_ARRAY_TYPE: int

def glAreTexturesResident(n: int, textures: UIntArray, residences: UByteArray | None = None) -> UByteArrayResult: ...
def glArrayElement(i: int) -> None: ...
def glBindTexture(target: int, texture: int) -> None: ...
def glColorPointer(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glCopyTexImage1D(target: int, level: int, internalformat: int, x: int, y: int, width: int, border: int) -> None: ...
def glCopyTexImage2D(target: int, level: int, internalformat: int, x: int, y: int, width: int, height: int, border: int) -> None: ...
def glCopyTexSubImage1D(target: int, level: int, xoffset: int, x: int, y: int, width: int) -> None: ...
def glCopyTexSubImage2D(target: int, level: int, xoffset: int, yoffset: int, x: int, y: int, width: int, height: int) -> None: ...
def glDeleteTextures(n: int, textures: UIntArray) -> None: ...
def glDisableClientState(array: int) -> None: ...
def glDrawArrays(mode: int, first: int, count: int) -> None: ...
def glDrawElements(mode: int, count: int, type: int, indices: AnyArray) -> None: ...
def glEdgeFlagPointer(stride: int, pointer: AnyArray) -> None: ...
def glEnableClientState(array: int) -> None: ...
def glGenTextures(n: int, textures: UIntArray | None = None) -> UIntArrayResult: ...
def glGetPointerv(pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glIndexPointer(type: int, stride: int, pointer: AnyArray) -> None: ...
def glIndexub(c: int) -> None: ...
def glIndexubv(c: UByteArray) -> None: ...
def glInterleavedArrays(format: int, stride: int, pointer: AnyArray) -> None: ...
def glIsTexture(texture: int) -> int: ...
def glNormalPointer(type: int, stride: int, pointer: AnyArray) -> None: ...
def glPolygonOffset(factor: float, units: float) -> None: ...
def glPopClientAttrib() -> None: ...
def glPrioritizeTextures(n: int, textures: UIntArray, priorities: FloatArray) -> None: ...
def glPushClientAttrib(mask: int) -> None: ...
def glTexCoordPointer(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glTexSubImage1D(target: int, level: int, xoffset: int, width: int, format: int, type: int, pixels: AnyArray) -> None: ...
def glTexSubImage2D(target: int, level: int, xoffset: int, yoffset: int, width: int, height: int, format: int, type: int, pixels: AnyArray) -> None: ...
def glVertexPointer(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...

def glInitGl11VERSION() -> bool: ...
GL_MODELVIEW0_EXT: int
GL_MODELVIEW0_MATRIX_EXT: int
GL_MODELVIEW0_STACK_DEPTH_EXT: int
GL_DEPTH_BUFFER: int
GL_STENCIL_BUFFER: int

def __getattr__(name: str) -> Any: ...
