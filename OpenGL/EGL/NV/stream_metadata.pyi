"""OpenGL.EGL.NV.stream_metadata -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import AnyArray, Int64Array

from OpenGL.raw.EGL._types import *

EGL_CONSUMER_METADATA_NV: int
EGL_MAX_STREAM_METADATA_BLOCKS_NV: int
EGL_MAX_STREAM_METADATA_BLOCK_SIZE_NV: int
EGL_MAX_STREAM_METADATA_TOTAL_SIZE_NV: int
EGL_METADATA0_SIZE_NV: int
EGL_METADATA0_TYPE_NV: int
EGL_METADATA1_SIZE_NV: int
EGL_METADATA1_TYPE_NV: int
EGL_METADATA2_SIZE_NV: int
EGL_METADATA2_TYPE_NV: int
EGL_METADATA3_SIZE_NV: int
EGL_METADATA3_TYPE_NV: int
EGL_PENDING_METADATA_NV: int
EGL_PRODUCER_METADATA_NV: int

def eglQueryDisplayAttribNV(dpy: Any, attribute: int, value: Int64Array) -> int: ...
def eglQueryStreamMetadataNV(dpy: Any, stream: Any, name: int, n: int, offset: int, size: int, data: AnyArray) -> int: ...
def eglSetStreamMetadataNV(dpy: Any, stream: Any, n: int, offset: int, size: int, data: AnyArray) -> int: ...

def glInitStreamMetadataNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
