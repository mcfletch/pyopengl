"""OpenGL.GLES1.EXT.robustness -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, FloatArray, IntArray

from OpenGL.raw.GLES1._types import *

GL_CONTEXT_ROBUST_ACCESS_EXT: int
GL_GUILTY_CONTEXT_RESET_EXT: int
GL_INNOCENT_CONTEXT_RESET_EXT: int
GL_LOSE_CONTEXT_ON_RESET_EXT: int
GL_NO_ERROR: int
GL_NO_RESET_NOTIFICATION_EXT: int
GL_RESET_NOTIFICATION_STRATEGY_EXT: int
GL_UNKNOWN_CONTEXT_RESET_EXT: int

def glGetGraphicsResetStatusEXT() -> int: ...
def glGetnUniformfvEXT(program: int, location: int, bufSize: int, params: FloatArray) -> None: ...
def glGetnUniformivEXT(program: int, location: int, bufSize: int, params: IntArray) -> None: ...
def glReadnPixelsEXT(x: int, y: int, width: int, height: int, format: int, type: int, bufSize: int, data: AnyArray) -> None: ...

def glInitRobustnessEXT() -> bool: ...

def __getattr__(name: str) -> Any: ...
