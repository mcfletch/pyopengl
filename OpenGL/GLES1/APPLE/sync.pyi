"""OpenGL.GLES1.APPLE.sync -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array, IntArray

from OpenGL.raw.GLES1._types import *

GL_ALREADY_SIGNALED_APPLE: int
GL_CONDITION_SATISFIED_APPLE: int
GL_MAX_SERVER_WAIT_TIMEOUT_APPLE: int
GL_OBJECT_TYPE_APPLE: int
GL_SIGNALED_APPLE: int
GL_SYNC_CONDITION_APPLE: int
GL_SYNC_FENCE_APPLE: int
GL_SYNC_FLAGS_APPLE: int
GL_SYNC_FLUSH_COMMANDS_BIT_APPLE: int
GL_SYNC_GPU_COMMANDS_COMPLETE_APPLE: int
GL_SYNC_OBJECT_APPLE: int
GL_SYNC_STATUS_APPLE: int
GL_TIMEOUT_EXPIRED_APPLE: int
GL_TIMEOUT_IGNORED_APPLE: int
GL_UNSIGNALED_APPLE: int
GL_WAIT_FAILED_APPLE: int

def glClientWaitSyncAPPLE(sync: Any, flags: int, timeout: int) -> int: ...
def glDeleteSyncAPPLE(sync: Any) -> None: ...
def glFenceSyncAPPLE(condition: int, flags: int) -> Any: ...
def glGetInteger64vAPPLE(pname: int, params: Int64Array) -> None: ...
def glGetSyncivAPPLE(sync: Any, pname: int, count: int, length: IntArray, values: IntArray) -> None: ...
def glIsSyncAPPLE(sync: Any) -> int: ...
def glWaitSyncAPPLE(sync: Any, flags: int, timeout: int) -> None: ...

def glInitSyncAPPLE() -> bool: ...

def __getattr__(name: str) -> Any: ...
