"""OpenGL.GLES2.KHR.debug -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, AnyArrayResult, ByteArray, ByteArrayResult, IntArray, IntArrayResult, UIntArray, UIntArrayResult

from OpenGL.raw.GLES2._types import *

GL_BUFFER: int
GL_BUFFER_KHR: int
GL_CONTEXT_FLAG_DEBUG_BIT: int
GL_CONTEXT_FLAG_DEBUG_BIT_KHR: int
GL_DEBUG_CALLBACK_FUNCTION: int
GL_DEBUG_CALLBACK_FUNCTION_KHR: int
GL_DEBUG_CALLBACK_USER_PARAM: int
GL_DEBUG_CALLBACK_USER_PARAM_KHR: int
GL_DEBUG_GROUP_STACK_DEPTH: int
GL_DEBUG_GROUP_STACK_DEPTH_KHR: int
GL_DEBUG_LOGGED_MESSAGES: int
GL_DEBUG_LOGGED_MESSAGES_KHR: int
GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH: int
GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH_KHR: int
GL_DEBUG_OUTPUT: int
GL_DEBUG_OUTPUT_KHR: int
GL_DEBUG_OUTPUT_SYNCHRONOUS: int
GL_DEBUG_OUTPUT_SYNCHRONOUS_KHR: int
GL_DEBUG_SEVERITY_HIGH: int
GL_DEBUG_SEVERITY_HIGH_KHR: int
GL_DEBUG_SEVERITY_LOW: int
GL_DEBUG_SEVERITY_LOW_KHR: int
GL_DEBUG_SEVERITY_MEDIUM: int
GL_DEBUG_SEVERITY_MEDIUM_KHR: int
GL_DEBUG_SEVERITY_NOTIFICATION: int
GL_DEBUG_SEVERITY_NOTIFICATION_KHR: int
GL_DEBUG_SOURCE_API: int
GL_DEBUG_SOURCE_API_KHR: int
GL_DEBUG_SOURCE_APPLICATION: int
GL_DEBUG_SOURCE_APPLICATION_KHR: int
GL_DEBUG_SOURCE_OTHER: int
GL_DEBUG_SOURCE_OTHER_KHR: int
GL_DEBUG_SOURCE_SHADER_COMPILER: int
GL_DEBUG_SOURCE_SHADER_COMPILER_KHR: int
GL_DEBUG_SOURCE_THIRD_PARTY: int
GL_DEBUG_SOURCE_THIRD_PARTY_KHR: int
GL_DEBUG_SOURCE_WINDOW_SYSTEM: int
GL_DEBUG_SOURCE_WINDOW_SYSTEM_KHR: int
GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR: int
GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR_KHR: int
GL_DEBUG_TYPE_ERROR: int
GL_DEBUG_TYPE_ERROR_KHR: int
GL_DEBUG_TYPE_MARKER: int
GL_DEBUG_TYPE_MARKER_KHR: int
GL_DEBUG_TYPE_OTHER: int
GL_DEBUG_TYPE_OTHER_KHR: int
GL_DEBUG_TYPE_PERFORMANCE: int
GL_DEBUG_TYPE_PERFORMANCE_KHR: int
GL_DEBUG_TYPE_POP_GROUP: int
GL_DEBUG_TYPE_POP_GROUP_KHR: int
GL_DEBUG_TYPE_PORTABILITY: int
GL_DEBUG_TYPE_PORTABILITY_KHR: int
GL_DEBUG_TYPE_PUSH_GROUP: int
GL_DEBUG_TYPE_PUSH_GROUP_KHR: int
GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR: int
GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR_KHR: int
GL_DISPLAY_LIST: int
GL_MAX_DEBUG_GROUP_STACK_DEPTH: int
GL_MAX_DEBUG_GROUP_STACK_DEPTH_KHR: int
GL_MAX_DEBUG_LOGGED_MESSAGES: int
GL_MAX_DEBUG_LOGGED_MESSAGES_KHR: int
GL_MAX_DEBUG_MESSAGE_LENGTH: int
GL_MAX_DEBUG_MESSAGE_LENGTH_KHR: int
GL_MAX_LABEL_LENGTH: int
GL_MAX_LABEL_LENGTH_KHR: int
GL_PROGRAM: int
GL_PROGRAM_KHR: int
GL_PROGRAM_PIPELINE: int
GL_PROGRAM_PIPELINE_KHR: int
GL_QUERY: int
GL_QUERY_KHR: int
GL_SAMPLER: int
GL_SAMPLER_KHR: int
GL_SHADER: int
GL_SHADER_KHR: int
GL_STACK_OVERFLOW: int
GL_STACK_OVERFLOW_KHR: int
GL_STACK_UNDERFLOW: int
GL_STACK_UNDERFLOW_KHR: int
GL_VERTEX_ARRAY: int
GL_VERTEX_ARRAY_KHR: int

def glDebugMessageCallback(callback: Any, userParam: AnyArray) -> None: ...
def glDebugMessageCallbackKHR(callback: Any, userParam: AnyArray) -> None: ...
def glDebugMessageControl(source: int, type: int, severity: int, count: int, ids: UIntArray, enabled: bool) -> None: ...
def glDebugMessageControlKHR(source: int, type: int, severity: int, count: int, ids: UIntArray, enabled: bool) -> None: ...
def glDebugMessageInsert(source: int, type: int, id: int, severity: int, length: int, buf: ByteArray) -> None: ...
def glDebugMessageInsertKHR(source: int, type: int, id: int, severity: int, length: int, buf: ByteArray) -> None: ...
def glGetDebugMessageLog(count: int, bufSize: int, sources: UIntArray | None = None, types: UIntArray | None = None, ids: UIntArray | None = None, severities: UIntArray | None = None, lengths: IntArray | None = None, messageLog: ByteArray | None = None) -> tuple[UIntArrayResult, IntArrayResult, ByteArrayResult, UIntArrayResult, UIntArrayResult, UIntArrayResult]: ...
def glGetDebugMessageLogKHR(count: int, bufSize: int, sources: UIntArray, types: UIntArray, ids: UIntArray, severities: UIntArray, lengths: IntArray, messageLog: ByteArray) -> int: ...
def glGetObjectLabel(identifier: int, name: int, bufSize: int, length: IntArray | None = None, label: ByteArray | None = None) -> tuple[ByteArrayResult, IntArrayResult]: ...
def glGetObjectLabelKHR(identifier: int, name: int, bufSize: int, length: IntArray, label: ByteArray) -> None: ...
def glGetObjectPtrLabel(ptr: AnyArray, bufSize: int, length: IntArray | None = None, label: ByteArray | None = None) -> tuple[ByteArrayResult, IntArrayResult]: ...
def glGetObjectPtrLabelKHR(ptr: AnyArray, bufSize: int, length: IntArray, label: ByteArray) -> None: ...
def glGetPointerv(pname: int, params: AnyArray | None = None) -> AnyArrayResult: ...
def glGetPointervKHR(pname: int, params: AnyArray) -> None: ...
def glObjectLabel(identifier: int, name: int, length: int, label: ByteArray) -> None: ...
def glObjectLabelKHR(identifier: int, name: int, length: int, label: ByteArray) -> None: ...
def glObjectPtrLabel(ptr: AnyArray, length: int, label: ByteArray) -> None: ...
def glObjectPtrLabelKHR(ptr: AnyArray, length: int, label: ByteArray) -> None: ...
def glPopDebugGroup() -> None: ...
def glPopDebugGroupKHR() -> None: ...
def glPushDebugGroup(source: int, id: int, length: int, message: ByteArray) -> None: ...
def glPushDebugGroupKHR(source: int, id: int, length: int, message: ByteArray) -> None: ...

def glInitDebugKHR() -> bool: ...

def __getattr__(name: str) -> Any: ...
