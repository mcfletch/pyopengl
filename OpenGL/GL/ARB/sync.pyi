"""OpenGL.GL.ARB.sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array, Int64ArrayResult, IntArray, IntArrayResult

from OpenGL.raw.GL._types import *

GL_ALREADY_SIGNALED: int
GL_CONDITION_SATISFIED: int
GL_MAX_SERVER_WAIT_TIMEOUT: int
GL_OBJECT_TYPE: int
GL_SIGNALED: int
GL_SYNC_CONDITION: int
GL_SYNC_FENCE: int
GL_SYNC_FLAGS: int
GL_SYNC_FLUSH_COMMANDS_BIT: int
GL_SYNC_GPU_COMMANDS_COMPLETE: int
GL_SYNC_STATUS: int
GL_TIMEOUT_EXPIRED: int
GL_TIMEOUT_IGNORED: int
GL_UNSIGNALED: int
GL_WAIT_FAILED: int

def glClientWaitSync(sync: Any, flags: int, timeout: int) -> int: ...
def glDeleteSync(sync: Any) -> None: ...
def glFenceSync(condition: int, flags: int) -> Any: ...
def glGetInteger64v(pname: int, data: Int64Array | None = None) -> Int64ArrayResult: ...
def glGetSynciv(sync: Any, pname: int, count: int, length: IntArray | None = None, values: IntArray | None = None) -> tuple[IntArrayResult, IntArrayResult]: ...
def glIsSync(sync: Any) -> int: ...
def glWaitSync(sync: Any, flags: int, timeout: int) -> None: ...

def glInitSyncARB() -> bool: ...
def glGetSync(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
