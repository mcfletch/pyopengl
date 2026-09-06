"""OpenGL.GL.ARB.debug_output -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GL._types import *

GL_DEBUG_CALLBACK_FUNCTION_ARB: int
GL_DEBUG_CALLBACK_USER_PARAM_ARB: int
GL_DEBUG_LOGGED_MESSAGES_ARB: int
GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH_ARB: int
GL_DEBUG_OUTPUT_SYNCHRONOUS_ARB: int
GL_DEBUG_SEVERITY_HIGH_ARB: int
GL_DEBUG_SEVERITY_LOW_ARB: int
GL_DEBUG_SEVERITY_MEDIUM_ARB: int
GL_DEBUG_SOURCE_API_ARB: int
GL_DEBUG_SOURCE_APPLICATION_ARB: int
GL_DEBUG_SOURCE_OTHER_ARB: int
GL_DEBUG_SOURCE_SHADER_COMPILER_ARB: int
GL_DEBUG_SOURCE_THIRD_PARTY_ARB: int
GL_DEBUG_SOURCE_WINDOW_SYSTEM_ARB: int
GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR_ARB: int
GL_DEBUG_TYPE_ERROR_ARB: int
GL_DEBUG_TYPE_OTHER_ARB: int
GL_DEBUG_TYPE_PERFORMANCE_ARB: int
GL_DEBUG_TYPE_PORTABILITY_ARB: int
GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR_ARB: int
GL_MAX_DEBUG_LOGGED_MESSAGES_ARB: int
GL_MAX_DEBUG_MESSAGE_LENGTH_ARB: int

def glDebugMessageCallbackARB(callback: Any, userParam: AnyArray) -> None: ...
def glDebugMessageControlARB(source: int, type: int, severity: int, count: int, ids: UIntArray, enabled: bool) -> None: ...
def glDebugMessageInsertARB(source: int, type: int, id: int, severity: int, length: int, buf: ByteArray) -> None: ...
def glGetDebugMessageLogARB(count: int, bufSize: int, sources: UIntArray | None = None, types: UIntArray | None = None, ids: UIntArray | None = None, severities: UIntArray | None = None, lengths: IntArray | None = None, messageLog: ByteArray | None = None) -> tuple[UIntArrayResult, IntArrayResult, ByteArrayResult, UIntArrayResult, UIntArrayResult, UIntArrayResult]: ...

def glInitDebugOutputARB() -> bool: ...

def __getattr__(name: str) -> Any: ...
