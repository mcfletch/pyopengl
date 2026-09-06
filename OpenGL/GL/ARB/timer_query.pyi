"""OpenGL.GL.ARB.timer_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array, Int64ArrayResult, UInt64Array, UInt64ArrayResult

from OpenGL.raw.GL._types import *

GL_TIMESTAMP: int
GL_TIME_ELAPSED: int

def glGetQueryObjecti64v(id: int, pname: int, params: Int64Array | None = None) -> Int64ArrayResult: ...
def glGetQueryObjectui64v(id: int, pname: int, params: UInt64Array | None = None) -> UInt64ArrayResult: ...
def glQueryCounter(id: int, target: int) -> None: ...

def glInitTimerQueryARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
