"""OpenGL.GL.ARB.internalformat_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_NUM_SAMPLE_COUNTS: int

def glGetInternalformativ(target: int, internalformat: int, pname: int, count: int, params: IntArray | None = None) -> IntArrayResult: ...

def glInitInternalformatQueryARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
