"""OpenGL.GL.ARB.vertex_blend -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, DoubleArray, FloatArray, IntArray, ShortArray, UByteArray, UIntArray, UShortArray

from OpenGL.raw.GL._types import *

GL_ACTIVE_VERTEX_UNITS_ARB: int
GL_CURRENT_WEIGHT_ARB: int
GL_MAX_VERTEX_UNITS_ARB: int
GL_MODELVIEW0_ARB: int
GL_MODELVIEW10_ARB: int
GL_MODELVIEW11_ARB: int
GL_MODELVIEW12_ARB: int
GL_MODELVIEW13_ARB: int
GL_MODELVIEW14_ARB: int
GL_MODELVIEW15_ARB: int
GL_MODELVIEW16_ARB: int
GL_MODELVIEW17_ARB: int
GL_MODELVIEW18_ARB: int
GL_MODELVIEW19_ARB: int
GL_MODELVIEW1_ARB: int
GL_MODELVIEW20_ARB: int
GL_MODELVIEW21_ARB: int
GL_MODELVIEW22_ARB: int
GL_MODELVIEW23_ARB: int
GL_MODELVIEW24_ARB: int
GL_MODELVIEW25_ARB: int
GL_MODELVIEW26_ARB: int
GL_MODELVIEW27_ARB: int
GL_MODELVIEW28_ARB: int
GL_MODELVIEW29_ARB: int
GL_MODELVIEW2_ARB: int
GL_MODELVIEW30_ARB: int
GL_MODELVIEW31_ARB: int
GL_MODELVIEW3_ARB: int
GL_MODELVIEW4_ARB: int
GL_MODELVIEW5_ARB: int
GL_MODELVIEW6_ARB: int
GL_MODELVIEW7_ARB: int
GL_MODELVIEW8_ARB: int
GL_MODELVIEW9_ARB: int
GL_VERTEX_BLEND_ARB: int
GL_WEIGHT_ARRAY_ARB: int
GL_WEIGHT_ARRAY_POINTER_ARB: int
GL_WEIGHT_ARRAY_SIZE_ARB: int
GL_WEIGHT_ARRAY_STRIDE_ARB: int
GL_WEIGHT_ARRAY_TYPE_ARB: int
GL_WEIGHT_SUM_UNITY_ARB: int

def glVertexBlendARB(count: int) -> None: ...
def glWeightPointerARB(size: int, type: int, stride: int, pointer: AnyArray) -> None: ...
def glWeightbvARB(size: int, weights: ByteArray) -> None: ...
def glWeightdvARB(size: int, weights: DoubleArray) -> None: ...
def glWeightfvARB(size: int, weights: FloatArray) -> None: ...
def glWeightivARB(size: int, weights: IntArray) -> None: ...
def glWeightsvARB(size: int, weights: ShortArray) -> None: ...
def glWeightubvARB(size: int, weights: UByteArray) -> None: ...
def glWeightuivARB(size: int, weights: UIntArray) -> None: ...
def glWeightusvARB(size: int, weights: UShortArray) -> None: ...

def glInitVertexBlendARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
