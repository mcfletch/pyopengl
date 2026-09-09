"""OpenGL.GL.VERSION.GL_1_3 -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, DoubleArray, FloatArray, IntArray, ShortArray

from OpenGL.raw.GL._types import *

GL_ACTIVE_TEXTURE: int
GL_ADD_SIGNED: int
GL_CLAMP_TO_BORDER: int
GL_CLIENT_ACTIVE_TEXTURE: int
GL_COMBINE: int
GL_COMBINE_ALPHA: int
GL_COMBINE_RGB: int
GL_COMPRESSED_ALPHA: int
GL_COMPRESSED_INTENSITY: int
GL_COMPRESSED_LUMINANCE: int
GL_COMPRESSED_LUMINANCE_ALPHA: int
GL_COMPRESSED_RGB: int
GL_COMPRESSED_RGBA: int
GL_COMPRESSED_TEXTURE_FORMATS: int
GL_CONSTANT: int
GL_DOT3_RGB: int
GL_DOT3_RGBA: int
GL_INTERPOLATE: int
GL_MAX_CUBE_MAP_TEXTURE_SIZE: int
GL_MAX_TEXTURE_UNITS: int
GL_MULTISAMPLE: int
GL_MULTISAMPLE_BIT: int
GL_NORMAL_MAP: int
GL_NUM_COMPRESSED_TEXTURE_FORMATS: int
GL_OPERAND0_ALPHA: int
GL_OPERAND0_RGB: int
GL_OPERAND1_ALPHA: int
GL_OPERAND1_RGB: int
GL_OPERAND2_ALPHA: int
GL_OPERAND2_RGB: int
GL_PREVIOUS: int
GL_PRIMARY_COLOR: int
GL_PROXY_TEXTURE_CUBE_MAP: int
GL_REFLECTION_MAP: int
GL_RGB_SCALE: int
GL_SAMPLES: int
GL_SAMPLE_ALPHA_TO_COVERAGE: int
GL_SAMPLE_ALPHA_TO_ONE: int
GL_SAMPLE_BUFFERS: int
GL_SAMPLE_COVERAGE: int
GL_SAMPLE_COVERAGE_INVERT: int
GL_SAMPLE_COVERAGE_VALUE: int
GL_SOURCE0_ALPHA: int
GL_SOURCE0_RGB: int
GL_SOURCE1_ALPHA: int
GL_SOURCE1_RGB: int
GL_SOURCE2_ALPHA: int
GL_SOURCE2_RGB: int
GL_SUBTRACT: int
GL_TEXTURE0: int
GL_TEXTURE1: int
GL_TEXTURE10: int
GL_TEXTURE11: int
GL_TEXTURE12: int
GL_TEXTURE13: int
GL_TEXTURE14: int
GL_TEXTURE15: int
GL_TEXTURE16: int
GL_TEXTURE17: int
GL_TEXTURE18: int
GL_TEXTURE19: int
GL_TEXTURE2: int
GL_TEXTURE20: int
GL_TEXTURE21: int
GL_TEXTURE22: int
GL_TEXTURE23: int
GL_TEXTURE24: int
GL_TEXTURE25: int
GL_TEXTURE26: int
GL_TEXTURE27: int
GL_TEXTURE28: int
GL_TEXTURE29: int
GL_TEXTURE3: int
GL_TEXTURE30: int
GL_TEXTURE31: int
GL_TEXTURE4: int
GL_TEXTURE5: int
GL_TEXTURE6: int
GL_TEXTURE7: int
GL_TEXTURE8: int
GL_TEXTURE9: int
GL_TEXTURE_BINDING_CUBE_MAP: int
GL_TEXTURE_COMPRESSED: int
GL_TEXTURE_COMPRESSED_IMAGE_SIZE: int
GL_TEXTURE_COMPRESSION_HINT: int
GL_TEXTURE_CUBE_MAP: int
GL_TEXTURE_CUBE_MAP_NEGATIVE_X: int
GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: int
GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: int
GL_TEXTURE_CUBE_MAP_POSITIVE_X: int
GL_TEXTURE_CUBE_MAP_POSITIVE_Y: int
GL_TEXTURE_CUBE_MAP_POSITIVE_Z: int
GL_TRANSPOSE_COLOR_MATRIX: int
GL_TRANSPOSE_MODELVIEW_MATRIX: int
GL_TRANSPOSE_PROJECTION_MATRIX: int
GL_TRANSPOSE_TEXTURE_MATRIX: int

def glActiveTexture(texture: int) -> None: ...
def glClientActiveTexture(texture: int) -> None: ...
def glCompressedTexImage1D(target: int, level: int, internalformat: int, width: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexImage2D(target: int, level: int, internalformat: int, width: int, height: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexImage3D(target: int, level: int, internalformat: int, width: int, height: int, depth: int, border: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage1D(target: int, level: int, xoffset: int, width: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage2D(target: int, level: int, xoffset: int, yoffset: int, width: int, height: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glCompressedTexSubImage3D(target: int, level: int, xoffset: int, yoffset: int, zoffset: int, width: int, height: int, depth: int, format: int, imageSize: int, data: AnyArray) -> None: ...
def glGetCompressedTexImage(target: int, level: int, img: AnyArray) -> None: ...
def glLoadTransposeMatrixd(m: DoubleArray) -> None: ...
def glLoadTransposeMatrixf(m: FloatArray) -> None: ...
def glMultTransposeMatrixd(m: DoubleArray) -> None: ...
def glMultTransposeMatrixf(m: FloatArray) -> None: ...
def glMultiTexCoord1d(target: int, s: float) -> None: ...
def glMultiTexCoord1dv(target: int, v: DoubleArray) -> None: ...
def glMultiTexCoord1f(target: int, s: float) -> None: ...
def glMultiTexCoord1fv(target: int, v: FloatArray) -> None: ...
def glMultiTexCoord1i(target: int, s: int) -> None: ...
def glMultiTexCoord1iv(target: int, v: IntArray) -> None: ...
def glMultiTexCoord1s(target: int, s: int) -> None: ...
def glMultiTexCoord1sv(target: int, v: ShortArray) -> None: ...
def glMultiTexCoord2d(target: int, s: float, t: float) -> None: ...
def glMultiTexCoord2dv(target: int, v: DoubleArray) -> None: ...
def glMultiTexCoord2f(target: int, s: float, t: float) -> None: ...
def glMultiTexCoord2fv(target: int, v: FloatArray) -> None: ...
def glMultiTexCoord2i(target: int, s: int, t: int) -> None: ...
def glMultiTexCoord2iv(target: int, v: IntArray) -> None: ...
def glMultiTexCoord2s(target: int, s: int, t: int) -> None: ...
def glMultiTexCoord2sv(target: int, v: ShortArray) -> None: ...
def glMultiTexCoord3d(target: int, s: float, t: float, r: float) -> None: ...
def glMultiTexCoord3dv(target: int, v: DoubleArray) -> None: ...
def glMultiTexCoord3f(target: int, s: float, t: float, r: float) -> None: ...
def glMultiTexCoord3fv(target: int, v: FloatArray) -> None: ...
def glMultiTexCoord3i(target: int, s: int, t: int, r: int) -> None: ...
def glMultiTexCoord3iv(target: int, v: IntArray) -> None: ...
def glMultiTexCoord3s(target: int, s: int, t: int, r: int) -> None: ...
def glMultiTexCoord3sv(target: int, v: ShortArray) -> None: ...
def glMultiTexCoord4d(target: int, s: float, t: float, r: float, q: float) -> None: ...
def glMultiTexCoord4dv(target: int, v: DoubleArray) -> None: ...
def glMultiTexCoord4f(target: int, s: float, t: float, r: float, q: float) -> None: ...
def glMultiTexCoord4fv(target: int, v: FloatArray) -> None: ...
def glMultiTexCoord4i(target: int, s: int, t: int, r: int, q: int) -> None: ...
def glMultiTexCoord4iv(target: int, v: IntArray) -> None: ...
def glMultiTexCoord4s(target: int, s: int, t: int, r: int, q: int) -> None: ...
def glMultiTexCoord4sv(target: int, v: ShortArray) -> None: ...
def glSampleCoverage(value: float, invert: int) -> None: ...

def glInitGl13VERSION() -> bool: ...
GL_SRC0_ALPHA: int
GL_SRC0_RGB: int
GL_SRC1_ALPHA: int
GL_SRC1_RGB: int
GL_SRC2_ALPHA: int
GL_SRC2_RGB: int

def __getattr__(name: str) -> Any: ...
