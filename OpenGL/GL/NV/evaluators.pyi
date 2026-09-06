"""OpenGL.GL.NV.evaluators -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_EVAL_2D_NV: int
GL_EVAL_FRACTIONAL_TESSELLATION_NV: int
GL_EVAL_TRIANGULAR_2D_NV: int
GL_EVAL_VERTEX_ATTRIB0_NV: int
GL_EVAL_VERTEX_ATTRIB10_NV: int
GL_EVAL_VERTEX_ATTRIB11_NV: int
GL_EVAL_VERTEX_ATTRIB12_NV: int
GL_EVAL_VERTEX_ATTRIB13_NV: int
GL_EVAL_VERTEX_ATTRIB14_NV: int
GL_EVAL_VERTEX_ATTRIB15_NV: int
GL_EVAL_VERTEX_ATTRIB1_NV: int
GL_EVAL_VERTEX_ATTRIB2_NV: int
GL_EVAL_VERTEX_ATTRIB3_NV: int
GL_EVAL_VERTEX_ATTRIB4_NV: int
GL_EVAL_VERTEX_ATTRIB5_NV: int
GL_EVAL_VERTEX_ATTRIB6_NV: int
GL_EVAL_VERTEX_ATTRIB7_NV: int
GL_EVAL_VERTEX_ATTRIB8_NV: int
GL_EVAL_VERTEX_ATTRIB9_NV: int
GL_MAP_ATTRIB_U_ORDER_NV: int
GL_MAP_ATTRIB_V_ORDER_NV: int
GL_MAP_TESSELLATION_NV: int
GL_MAX_MAP_TESSELLATION_NV: int
GL_MAX_RATIONAL_EVAL_ORDER_NV: int

def glEvalMapsNV(target: int, mode: int) -> None: ...
def glGetMapAttribParameterfvNV(target: int, index: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetMapAttribParameterivNV(target: int, index: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetMapControlPointsNV(target: int, index: int, type: int, ustride: int, vstride: int, packed: bool, points: AnyArray | None = None) -> AnyArrayResult: ...
def glGetMapParameterfvNV(target: int, pname: int, params: FloatArray) -> None: ...
def glGetMapParameterivNV(target: int, pname: int, params: IntArray) -> None: ...
def glMapControlPointsNV(target: int, index: int, type: int, ustride: int, vstride: int, uorder: int, vorder: int, packed: bool, points: AnyArray) -> None: ...
def glMapParameterfvNV(target: int, pname: int, params: FloatArray) -> None: ...
def glMapParameterivNV(target: int, pname: int, params: IntArray) -> None: ...

def glInitEvaluatorsNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
