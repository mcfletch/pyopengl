"""OpenGL.GLES2.NV.timeline_semaphore -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, UIntArray

from OpenGL.raw.GLES2._types import *

GL_MAX_TIMELINE_SEMAPHORE_VALUE_DIFFERENCE_NV: int
GL_SEMAPHORE_TYPE_BINARY_NV: int
GL_SEMAPHORE_TYPE_NV: int
GL_SEMAPHORE_TYPE_TIMELINE_NV: int
GL_TIMELINE_SEMAPHORE_VALUE_NV: int

def glCreateSemaphoresNV(n: int, semaphores: UIntArray) -> None: ...
def glGetSemaphoreParameterivNV(semaphore: int, pname: int, params: IntArray) -> None: ...
def glSemaphoreParameterivNV(semaphore: int, pname: int, params: IntArray) -> None: ...

def glInitTimelineSemaphoreNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
