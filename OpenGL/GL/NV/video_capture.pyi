"""OpenGL.GL.NV.video_capture -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import DoubleArray, DoubleArrayResult, FloatArray, FloatArrayResult, IntArray, IntArrayResult, UInt64Array, UIntArray

from OpenGL.raw.GL._types import *

GL_FAILURE_NV: int
GL_FIELD_LOWER_NV: int
GL_FIELD_UPPER_NV: int
GL_LAST_VIDEO_CAPTURE_STATUS_NV: int
GL_NEXT_VIDEO_CAPTURE_BUFFER_STATUS_NV: int
GL_NUM_VIDEO_CAPTURE_STREAMS_NV: int
GL_PARTIAL_SUCCESS_NV: int
GL_SUCCESS_NV: int
GL_VIDEO_BUFFER_BINDING_NV: int
GL_VIDEO_BUFFER_INTERNAL_FORMAT_NV: int
GL_VIDEO_BUFFER_NV: int
GL_VIDEO_BUFFER_PITCH_NV: int
GL_VIDEO_CAPTURE_FIELD_LOWER_HEIGHT_NV: int
GL_VIDEO_CAPTURE_FIELD_UPPER_HEIGHT_NV: int
GL_VIDEO_CAPTURE_FRAME_HEIGHT_NV: int
GL_VIDEO_CAPTURE_FRAME_WIDTH_NV: int
GL_VIDEO_CAPTURE_SURFACE_ORIGIN_NV: int
GL_VIDEO_CAPTURE_TO_422_SUPPORTED_NV: int
GL_VIDEO_COLOR_CONVERSION_MATRIX_NV: int
GL_VIDEO_COLOR_CONVERSION_MAX_NV: int
GL_VIDEO_COLOR_CONVERSION_MIN_NV: int
GL_VIDEO_COLOR_CONVERSION_OFFSET_NV: int
GL_YCBAYCR8A_4224_NV: int
GL_YCBYCR8_422_NV: int
GL_Z4Y12Z4CB12Z4A12Z4Y12Z4CR12Z4A12_4224_NV: int
GL_Z4Y12Z4CB12Z4CR12_444_NV: int
GL_Z4Y12Z4CB12Z4Y12Z4CR12_422_NV: int
GL_Z6Y10Z6CB10Z6A10Z6Y10Z6CR10Z6A10_4224_NV: int
GL_Z6Y10Z6CB10Z6Y10Z6CR10_422_NV: int

def glBeginVideoCaptureNV(video_capture_slot: int) -> None: ...
def glBindVideoCaptureStreamBufferNV(video_capture_slot: int, stream: int, frame_region: int, offset: int) -> None: ...
def glBindVideoCaptureStreamTextureNV(video_capture_slot: int, stream: int, frame_region: int, target: int, texture: int) -> None: ...
def glEndVideoCaptureNV(video_capture_slot: int) -> None: ...
def glGetVideoCaptureStreamdvNV(video_capture_slot: int, stream: int, pname: int, params: DoubleArray | None = None) -> DoubleArrayResult: ...
def glGetVideoCaptureStreamfvNV(video_capture_slot: int, stream: int, pname: int, params: FloatArray | None = None) -> FloatArrayResult: ...
def glGetVideoCaptureStreamivNV(video_capture_slot: int, stream: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glGetVideoCaptureivNV(video_capture_slot: int, pname: int, params: IntArray | None = None) -> IntArrayResult: ...
def glVideoCaptureNV(video_capture_slot: int, sequence_num: UIntArray, capture_time: UInt64Array) -> int: ...
def glVideoCaptureStreamParameterdvNV(video_capture_slot: int, stream: int, pname: int, params: DoubleArray) -> None: ...
def glVideoCaptureStreamParameterfvNV(video_capture_slot: int, stream: int, pname: int, params: FloatArray) -> None: ...
def glVideoCaptureStreamParameterivNV(video_capture_slot: int, stream: int, pname: int, params: IntArray) -> None: ...

def glInitVideoCaptureNV() -> bool: ...

def __getattr__(name: str) -> Any: ...
