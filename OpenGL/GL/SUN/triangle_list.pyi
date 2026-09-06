"""OpenGL.GL.SUN.triangle_list -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, UByteArray, UIntArray, UShortArray

from OpenGL.raw.GL._types import *

GL_R1UI_C3F_V3F_SUN: int
GL_R1UI_C4F_N3F_V3F_SUN: int
GL_R1UI_C4UB_V3F_SUN: int
GL_R1UI_N3F_V3F_SUN: int
GL_R1UI_T2F_C4F_N3F_V3F_SUN: int
GL_R1UI_T2F_N3F_V3F_SUN: int
GL_R1UI_T2F_V3F_SUN: int
GL_R1UI_V3F_SUN: int
GL_REPLACEMENT_CODE_ARRAY_POINTER_SUN: int
GL_REPLACEMENT_CODE_ARRAY_STRIDE_SUN: int
GL_REPLACEMENT_CODE_ARRAY_SUN: int
GL_REPLACEMENT_CODE_ARRAY_TYPE_SUN: int
GL_REPLACEMENT_CODE_SUN: int
GL_REPLACE_MIDDLE_SUN: int
GL_REPLACE_OLDEST_SUN: int
GL_RESTART_SUN: int
GL_TRIANGLE_LIST_SUN: int

def glReplacementCodePointerSUN(type: int, stride: int, pointer: AnyArray) -> None: ...
def glReplacementCodeubSUN(code: int) -> None: ...
def glReplacementCodeubvSUN(code: UByteArray) -> None: ...
def glReplacementCodeuiSUN(code: int) -> None: ...
def glReplacementCodeuivSUN(code: UIntArray) -> None: ...
def glReplacementCodeusSUN(code: int) -> None: ...
def glReplacementCodeusvSUN(code: UShortArray) -> None: ...

def glInitTriangleListSUN() -> bool: ...

def __getattr__(name: str) -> Any: ...
