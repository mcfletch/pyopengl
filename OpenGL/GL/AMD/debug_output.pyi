"""OpenGL.GL.AMD.debug_output -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_DEBUG_CATEGORY_API_ERROR_AMD: int
GL_DEBUG_CATEGORY_APPLICATION_AMD: int
GL_DEBUG_CATEGORY_DEPRECATION_AMD: int
GL_DEBUG_CATEGORY_OTHER_AMD: int
GL_DEBUG_CATEGORY_PERFORMANCE_AMD: int
GL_DEBUG_CATEGORY_SHADER_COMPILER_AMD: int
GL_DEBUG_CATEGORY_UNDEFINED_BEHAVIOR_AMD: int
GL_DEBUG_CATEGORY_WINDOW_SYSTEM_AMD: int
GL_DEBUG_LOGGED_MESSAGES_AMD: int
GL_DEBUG_SEVERITY_HIGH_AMD: int
GL_DEBUG_SEVERITY_LOW_AMD: int
GL_DEBUG_SEVERITY_MEDIUM_AMD: int
GL_MAX_DEBUG_LOGGED_MESSAGES_AMD: int
GL_MAX_DEBUG_MESSAGE_LENGTH_AMD: int

def glDebugMessageCallbackAMD(callback: Any, userParam: AnyArray) -> None: ...
def glDebugMessageEnableAMD(category: int, severity: int, count: int, ids: UIntArray, enabled: bool) -> None: ...
def glDebugMessageInsertAMD(category: int, severity: int, id: int, length: int, buf: ByteArray) -> None: ...
def glGetDebugMessageLogAMD(count: int, bufSize: int, categories: UIntArray | None = None, severities: UIntArray | None = None, ids: UIntArray | None = None, lengths: IntArray | None = None, message: ByteArray | None = None) -> tuple[UIntArrayResult, UIntArrayResult, IntArrayResult, ByteArrayResult, UIntArrayResult]: ...

def glInitDebugOutputAMD() -> bool: ...

def __getattr__(name: str) -> Any: ...
