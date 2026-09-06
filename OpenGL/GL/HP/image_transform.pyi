"""OpenGL.GL.HP.image_transform -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import FloatArray, FloatArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_AVERAGE_HP: int
GL_CUBIC_HP: int
GL_IMAGE_CUBIC_WEIGHT_HP: int
GL_IMAGE_MAG_FILTER_HP: int
GL_IMAGE_MIN_FILTER_HP: int
GL_IMAGE_ROTATE_ANGLE_HP: int
GL_IMAGE_ROTATE_ORIGIN_X_HP: int
GL_IMAGE_ROTATE_ORIGIN_Y_HP: int
GL_IMAGE_SCALE_X_HP: int
GL_IMAGE_SCALE_Y_HP: int
GL_IMAGE_TRANSFORM_2D_HP: int
GL_IMAGE_TRANSLATE_X_HP: int
GL_IMAGE_TRANSLATE_Y_HP: int
GL_POST_IMAGE_TRANSFORM_COLOR_TABLE_HP: int
GL_PROXY_POST_IMAGE_TRANSFORM_COLOR_TABLE_HP: int

def glGetImageTransformParameterfvHP(target: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetImageTransformParameterivHP(target: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glImageTransformParameterfHP(target: int, pname: int, param: float) -> None: ...
def glImageTransformParameterfvHP(target: int, pname: int, params: FloatArray) -> None: ...
def glImageTransformParameteriHP(target: int, pname: int, param: int) -> None: ...
def glImageTransformParameterivHP(target: int, pname: int, params: IntArray) -> None: ...

def glInitImageTransformHP() -> bool: ...

def __getattr__(name: str) -> Any: ...
