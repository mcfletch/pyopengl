"""OpenGL.GLES2.QCOM.alpha_test -- generated; regenerate with src/regenerate_c.py."""

from typing import Any

from OpenGL.raw.GLES2._types import *

GL_ALPHA_TEST_FUNC_QCOM: int
GL_ALPHA_TEST_QCOM: int
GL_ALPHA_TEST_REF_QCOM: int

def glAlphaFuncQCOM(func: int, ref: float) -> None: ...

def glInitAlphaTestQCOM() -> bool: ...

def __getattr__(name: str) -> Any: ...
