"""OpenGL.EGL.ANDROID.get_frame_timestamps -- generated; regenerate with src/regenerate_c.py."""

from typing import Any
from OpenGL._typing import Int64Array, IntArray, UInt64Array

from OpenGL.raw.EGL._types import *

EGL_COMPOSITE_DEADLINE_ANDROID: int
EGL_COMPOSITE_INTERVAL_ANDROID: int
EGL_COMPOSITE_TO_PRESENT_LATENCY_ANDROID: int
EGL_COMPOSITION_LATCH_TIME_ANDROID: int
EGL_DEQUEUE_READY_TIME_ANDROID: int
EGL_DISPLAY_PRESENT_TIME_ANDROID: int
EGL_FIRST_COMPOSITION_GPU_FINISHED_TIME_ANDROID: int
EGL_FIRST_COMPOSITION_START_TIME_ANDROID: int
EGL_LAST_COMPOSITION_START_TIME_ANDROID: int
EGL_READS_DONE_TIME_ANDROID: int
EGL_RENDERING_COMPLETE_TIME_ANDROID: int
EGL_REQUESTED_PRESENT_TIME_ANDROID: int
EGL_TIMESTAMPS_ANDROID: int
EGL_TIMESTAMP_INVALID_ANDROID: int
EGL_TIMESTAMP_PENDING_ANDROID: int

def eglGetCompositorTimingANDROID(dpy: Any, surface: Any, numTimestamps: int, names: IntArray, values: Int64Array) -> int: ...
def eglGetCompositorTimingSupportedANDROID(dpy: Any, surface: Any, name: int) -> int: ...
def eglGetFrameTimestampSupportedANDROID(dpy: Any, surface: Any, timestamp: int) -> int: ...
def eglGetFrameTimestampsANDROID(dpy: Any, surface: Any, frameId: int, numTimestamps: int, timestamps: IntArray, values: Int64Array) -> int: ...
def eglGetNextFrameIdANDROID(dpy: Any, surface: Any, frameId: UInt64Array) -> int: ...

def eglInitGetFrameTimestampsANDROID(*args: Any, **named: Any) -> Any: ...

def __getattr__(name: str) -> Any: ...
