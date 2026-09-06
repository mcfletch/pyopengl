"""OpenGL.GL.SGIX.polynomial_ffd -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import DoubleArray, FloatArray

from OpenGL.raw.GL._types import *

GL_DEFORMATIONS_MASK_SGIX: int
GL_GEOMETRY_DEFORMATION_BIT_SGIX: int
GL_GEOMETRY_DEFORMATION_SGIX: int
GL_MAX_DEFORMATION_ORDER_SGIX: int
GL_TEXTURE_DEFORMATION_BIT_SGIX: int
GL_TEXTURE_DEFORMATION_SGIX: int

def glDeformSGIX(mask: int) -> None: ...
def glDeformationMap3dSGIX(target: int, u1: float, u2: float, ustride: int, uorder: int, v1: float, v2: float, vstride: int, vorder: int, w1: float, w2: float, wstride: int, worder: int, points: DoubleArray) -> None: ...
def glDeformationMap3fSGIX(target: int, u1: float, u2: float, ustride: int, uorder: int, v1: float, v2: float, vstride: int, vorder: int, w1: float, w2: float, wstride: int, worder: int, points: FloatArray) -> None: ...
def glLoadIdentityDeformationMapSGIX(mask: int) -> None: ...

def glInitPolynomialFfdSGIX() -> bool: ...

def __getattr__(name: str) -> Any: ...
