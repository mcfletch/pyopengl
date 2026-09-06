"""OpenGL.GL.INTEL.performance_query -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, ByteArray, UInt64Array, UIntArray

from OpenGL.raw.GL._types import *

GL_PERFQUERY_COUNTER_DATA_BOOL32_INTEL: int
GL_PERFQUERY_COUNTER_DATA_DOUBLE_INTEL: int
GL_PERFQUERY_COUNTER_DATA_FLOAT_INTEL: int
GL_PERFQUERY_COUNTER_DATA_UINT32_INTEL: int
GL_PERFQUERY_COUNTER_DATA_UINT64_INTEL: int
GL_PERFQUERY_COUNTER_DESC_LENGTH_MAX_INTEL: int
GL_PERFQUERY_COUNTER_DURATION_NORM_INTEL: int
GL_PERFQUERY_COUNTER_DURATION_RAW_INTEL: int
GL_PERFQUERY_COUNTER_EVENT_INTEL: int
GL_PERFQUERY_COUNTER_NAME_LENGTH_MAX_INTEL: int
GL_PERFQUERY_COUNTER_RAW_INTEL: int
GL_PERFQUERY_COUNTER_THROUGHPUT_INTEL: int
GL_PERFQUERY_COUNTER_TIMESTAMP_INTEL: int
GL_PERFQUERY_DONOT_FLUSH_INTEL: int
GL_PERFQUERY_FLUSH_INTEL: int
GL_PERFQUERY_GLOBAL_CONTEXT_INTEL: int
GL_PERFQUERY_GPA_EXTENDED_COUNTERS_INTEL: int
GL_PERFQUERY_QUERY_NAME_LENGTH_MAX_INTEL: int
GL_PERFQUERY_SINGLE_CONTEXT_INTEL: int
GL_PERFQUERY_WAIT_INTEL: int

def glBeginPerfQueryINTEL(queryHandle: int) -> None: ...
def glCreatePerfQueryINTEL(queryId: int, queryHandle: UIntArray) -> None: ...
def glDeletePerfQueryINTEL(queryHandle: int) -> None: ...
def glEndPerfQueryINTEL(queryHandle: int) -> None: ...
def glGetFirstPerfQueryIdINTEL(queryId: UIntArray) -> None: ...
def glGetNextPerfQueryIdINTEL(queryId: int, nextQueryId: UIntArray) -> None: ...
def glGetPerfCounterInfoINTEL(queryId: int, counterId: int, counterNameLength: int, counterName: ByteArray, counterDescLength: int, counterDesc: ByteArray, counterOffset: UIntArray, counterDataSize: UIntArray, counterTypeEnum: UIntArray, counterDataTypeEnum: UIntArray, rawCounterMaxValue: UInt64Array) -> None: ...
def glGetPerfQueryDataINTEL(queryHandle: int, flags: int, dataSize: int, data: AnyArray, bytesWritten: UIntArray) -> None: ...
def glGetPerfQueryIdByNameINTEL(queryName: ByteArray, queryId: UIntArray) -> None: ...
def glGetPerfQueryInfoINTEL(queryId: int, queryNameLength: int, queryName: ByteArray, dataSize: UIntArray, noCounters: UIntArray, noInstances: UIntArray, capsMask: UIntArray) -> None: ...

def glInitPerformanceQueryINTEL() -> bool: ...

def __getattr__(name: str) -> Any: ...
